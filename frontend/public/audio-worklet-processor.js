/**
 * AudioWorklet processor that resamples audio to 16kHz and outputs Int16 PCM.
 * Runs in the audio rendering thread for low-latency capture.
 */
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this._buffer = new Float32Array(0)
  }

  process(inputs) {
    const input = inputs[0]
    if (!input || !input[0]) return true

    const channelData = input[0] // mono or first channel

    // Accumulate samples
    const newBuffer = new Float32Array(this._buffer.length + channelData.length)
    newBuffer.set(this._buffer)
    newBuffer.set(channelData, this._buffer.length)
    this._buffer = newBuffer

    // Resample from sampleRate to 16000 and send in chunks
    const ratio = sampleRate / 16000
    const outputSamples = Math.floor(this._buffer.length / ratio)

    if (outputSamples > 0) {
      const pcm16 = new Int16Array(outputSamples)
      for (let i = 0; i < outputSamples; i++) {
        const srcIndex = Math.floor(i * ratio)
        const sample = Math.max(-1, Math.min(1, this._buffer[srcIndex]))
        pcm16[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
      }

      // Keep remaining samples
      const consumed = Math.floor(outputSamples * ratio)
      this._buffer = this._buffer.slice(consumed)

      // Post PCM data to main thread
      this.port.postMessage(pcm16.buffer, [pcm16.buffer])
    }

    return true
  }
}

registerProcessor('pcm-processor', PCMProcessor)
