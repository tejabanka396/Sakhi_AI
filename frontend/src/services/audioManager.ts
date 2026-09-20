import { voiceService } from './voice';

export type PlaybackState = 'IDLE' | 'GENERATING' | 'QUEUED' | 'PLAYING' | 'CANCELLING' | 'ERROR';

export interface QueueItem {
  id: string; // response_id or message_id
  text: string;
  voiceId: string;
  language?: string;
  isPreview?: boolean;
}

export type StateListener = (state: PlaybackState, frequency: number) => void;

class AudioManager {
  private static instance: AudioManager;

  private audio: HTMLAudioElement | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private sourceNode: MediaElementAudioSourceNode | null = null;
  private animationFrameId: number | null = null;

  private state: PlaybackState = 'IDLE';
  private frequency: number = 0;
  private queue: QueueItem[] = [];
  private activeItem: QueueItem | null = null;

  // Deduplication tracker: Set of processed response IDs
  private processedResponseIds: Set<string> = new Set();
  
  // Abort / Cancellation sequence token to ignore stale in-flight fetches
  private generationSeq: number = 0;

  // Active object URL to revoke on cleanup
  private currentObjectUrl: string | null = null;

  // Registered state change listeners
  private listeners: Set<StateListener> = new Set();

  private constructor() {
    if (typeof window !== 'undefined') {
      this.initAudioElement();
    }
  }

  public static getInstance(): AudioManager {
    if (!AudioManager.instance) {
      AudioManager.instance = new AudioManager();
    }
    return AudioManager.instance;
  }

  private initAudioElement() {
    if (this.audio) return;

    this.audio = new Audio();
    this.audio.preload = 'auto';

    this.audio.addEventListener('ended', () => {
      this.handleAudioEnded();
    });

    this.audio.addEventListener('error', (e) => {
      console.warn('Central audio playback error:', e);
      this.handleAudioError();
    });
  }

  public subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);
    // Immediate callback with current state
    listener(this.state, this.frequency);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.state, this.frequency);
      } catch (err) {
        console.error('Error in AudioManager listener:', err);
      }
    }
  }

  private setState(newState: PlaybackState) {
    this.state = newState;
    this.notify();
  }

  public getState(): PlaybackState {
    return this.state;
  }

  public isSpeaking(): boolean {
    return this.state === 'PLAYING';
  }

  public getFrequency(): number {
    return this.frequency;
  }

  private initWebAudio() {
    if (!this.audio || this.sourceNode) return;

    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;

      if (!this.audioContext) {
        this.audioContext = new AudioCtx();
      }
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume().catch(() => {});
      }

      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;

      this.sourceNode = this.audioContext.createMediaElementSource(this.audio);
      this.sourceNode.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
    } catch (e) {
      console.warn('Web Audio initialization fallback:', e);
    }
  }

  private startFrequencyLoop() {
    this.stopFrequencyLoop();

    const update = () => {
      if (this.state !== 'PLAYING') {
        this.frequency = 0;
        this.notify();
        return;
      }

      if (this.analyser) {
        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        this.frequency = Math.min(1, avg / 70);
      } else {
        // Natural speech frequency variance fallback
        this.frequency = 0.3 + Math.random() * 0.5;
      }

      this.notify();
      this.animationFrameId = requestAnimationFrame(update);
    };

    this.animationFrameId = requestAnimationFrame(update);
  }

  private stopFrequencyLoop() {
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.frequency = 0;
  }

  /**
   * Request TTS playback for an AI response.
   * Strictly enforces deduplication: duplicate response_id is ignored.
   */
  public async speak(
    responseId: string,
    speechText: string,
    voiceId: string = 'female_voice',
    language: string = 'auto'
  ): Promise<void> {
    if (!speechText || !speechText.trim()) {
      return;
    }

    // 1. Strict Deduplication Check
    if (responseId && this.processedResponseIds.has(responseId)) {
      console.warn(`[AudioManager] Duplicate response ID '${responseId}' ignored.`);
      return;
    }

    if (responseId) {
      this.processedResponseIds.add(responseId);
      // Keep set size bounded to prevent unbounded memory growth in long sessions
      if (this.processedResponseIds.size > 200) {
        const first = this.processedResponseIds.values().next().value;
        if (first) this.processedResponseIds.delete(first);
      }
    }

    // 2. Interrupt any ongoing playback and clear old queue
    this.stop();

    const item: QueueItem = {
      id: responseId || `req_${Date.now()}`,
      text: speechText.trim(),
      voiceId,
      language,
      isPreview: false
    };

    this.queue.push(item);
    this.processNextInQueue();
  }

  /**
   * Preview a voice without adding to conversation history.
   * Cancels active playback and plays preview through central player.
   */
  public async previewVoice(voiceId: string): Promise<void> {
    this.stop();

    const previewItem: QueueItem = {
      id: `preview_${voiceId}_${Date.now()}`,
      text: '', // Preview URL endpoint provides canonical sentence
      voiceId,
      isPreview: true
    };

    this.queue.push(previewItem);
    this.processNextInQueue();
  }

  private async processNextInQueue() {
    if (this.queue.length === 0) {
      this.activeItem = null;
      this.setState('IDLE');
      return;
    }

    const item = this.queue.shift()!;
    this.activeItem = item;
    const currentSeq = ++this.generationSeq;

    this.setState('GENERATING');

    try {
      let audioBlob: Blob;

      if (item.isPreview) {
        // Direct fetch of preview audio
        const previewUrl = voiceService.getPreviewUrl(item.voiceId);
        const res = await fetch(previewUrl);
        if (!res.ok) throw new Error(`Preview fetch failed: ${res.statusText}`);
        audioBlob = await res.blob();
      } else {
        // Synthesize response speech text
        audioBlob = await voiceService.synthesize(item.text, item.voiceId, item.language);
      }

      // Check if cancelled/superseded while fetching
      if (currentSeq !== this.generationSeq) {
        return;
      }

      if (!audioBlob || audioBlob.size === 0) {
        this.processNextInQueue();
        return;
      }

      this.cleanupCurrentObjectUrl();
      this.currentObjectUrl = URL.createObjectURL(audioBlob);

      if (!this.audio) {
        this.initAudioElement();
      }

      if (this.audio) {
        this.audio.src = this.currentObjectUrl;
        this.initWebAudio();

        await this.audio.play();

        // Check again if cancelled immediately after play start
        if (currentSeq !== this.generationSeq) {
          this.audio.pause();
          this.audio.src = '';
          return;
        }

        this.setState('PLAYING');
        this.startFrequencyLoop();
      }
    } catch (err) {
      if (currentSeq === this.generationSeq) {
        console.warn('[AudioManager] Synthesis or playback error:', err);
        this.cleanupCurrentObjectUrl();
        this.stopFrequencyLoop();
        this.setState('ERROR');
        // Return to IDLE after brief error flash
        setTimeout(() => {
          if (this.state === 'ERROR') {
            this.setState('IDLE');
          }
        }, 1200);
      }
    }
  }

  private handleAudioEnded() {
    this.cleanupCurrentObjectUrl();
    this.stopFrequencyLoop();

    if (this.queue.length > 0) {
      this.processNextInQueue();
    } else {
      this.activeItem = null;
      this.setState('IDLE');
    }
  }

  private handleAudioError() {
    this.cleanupCurrentObjectUrl();
    this.stopFrequencyLoop();
    this.activeItem = null;
    this.setState('IDLE');
  }

  private cleanupCurrentObjectUrl() {
    if (this.currentObjectUrl) {
      URL.revokeObjectURL(this.currentObjectUrl);
      this.currentObjectUrl = null;
    }
  }

  /**
   * Immediately stops playback, cancels in-flight fetches, and resets audio state.
   */
  public stop() {
    this.generationSeq++; // Invalidate pending fetches
    this.queue = [];
    this.activeItem = null;

    if (this.audio) {
      try {
        this.audio.pause();
        this.audio.currentTime = 0;
        this.audio.src = '';
      } catch (e) {
        // Ignore audio pause errors on unmounted elements
      }
    }

    this.cleanupCurrentObjectUrl();
    this.stopFrequencyLoop();
    this.setState('IDLE');
  }

  /**
   * Interrupts playback and resets for user input.
   */
  public interrupt() {
    this.stop();
  }
}

export const audioManager = AudioManager.getInstance();
