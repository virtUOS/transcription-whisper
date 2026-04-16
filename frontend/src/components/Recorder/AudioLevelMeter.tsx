import { useEffect, useRef, useState } from 'react'

interface AudioLevelMeterProps {
  stream: MediaStream | null
}

export function AudioLevelMeter({ stream }: AudioLevelMeterProps) {
  const [level, setLevel] = useState(0)
  const animFrameRef = useRef<number>(0)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const contextRef = useRef<AudioContext | null>(null)

  const [prevStream, setPrevStream] = useState(stream)
  if (stream !== prevStream) {
    setPrevStream(stream)
    if (!stream) setLevel(0)
  }

  useEffect(() => {
    if (!stream) return

    const audioContext = new AudioContext()
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 256
    const source = audioContext.createMediaStreamSource(stream)
    source.connect(analyser)

    contextRef.current = audioContext
    analyserRef.current = analyser

    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const tick = () => {
      analyser.getByteFrequencyData(dataArray)
      // Average of frequency data, normalized to 0-1
      const avg = dataArray.reduce((sum, v) => sum + v, 0) / dataArray.length / 255
      setLevel(avg)
      animFrameRef.current = requestAnimationFrame(tick)
    }
    tick()

    return () => {
      cancelAnimationFrame(animFrameRef.current)
      source.disconnect()
      audioContext.close()
    }
  }, [stream])

  return (
    <div className="w-full h-6 bg-gray-700 rounded-full overflow-hidden">
      <div
        className="h-full bg-green-500 rounded-full transition-all duration-100"
        // 3x gain: raw mic levels are typically low (0.1-0.3), so amplify for visible feedback
        style={{ width: `${Math.min(level * 100 * 3, 100)}%` }}
      />
    </div>
  )
}
