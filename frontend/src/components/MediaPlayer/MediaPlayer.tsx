import { useEffect, useRef, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import { useStore } from '../../store'
import type { Utterance } from '../../api/types'

function formatVttTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000)
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  const millis = ms % 1000
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(millis).padStart(3, '0')}`
}

function generateVtt(utterances: Utterance[], speakerMappings: Record<string, string>): string {
  let vtt = 'WEBVTT\n\n'
  for (const u of utterances) {
    const start = formatVttTime(u.start)
    const end = formatVttTime(u.end)
    const speaker = u.speaker ? (speakerMappings[u.speaker] || u.speaker) : ''
    const prefix = speaker ? `[${speaker}]: ` : ''
    vtt += `${start} --> ${end}\n${prefix}${u.text}\n\n`
  }
  return vtt
}

interface Props {
  fileId: string
  mediaType: string
}

export function MediaPlayer({ fileId, mediaType }: Props) {
  const { t } = useTranslation()
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const playerRef = useRef<ReturnType<typeof videojs> | null>(null)
  const trackRef = useRef<HTMLTrackElement | null>(null)
  const blobUrlRef = useRef<string | null>(null)
  const setCurrentTime = useStore((s) => s.setCurrentTime)
  const seekTo = useStore((s) => s.seekTo)
  const setSeekTo = useStore((s) => s.setSeekTo)
  const transcriptionResult = useStore((s) => s.transcriptionResult)
  const speakerMappings = useStore((s) => s.speakerMappings)

  const isVideo = mediaType === 'mp4' || mediaType === 'webm'
  const mimeTypes: Record<string, string> = {
    mp4: 'video/mp4',
    webm: 'video/webm',
    mp3: 'audio/mpeg',
    wav: 'audio/wav',
  }
  const mediaUrl = `/api/media/${fileId}`

  useEffect(() => {
    if (!videoRef.current) return

    const player = videojs(videoRef.current, {
      controls: true,
      responsive: true,
      fluid: !isVideo,
      sources: [{
        src: mediaUrl,
        type: mimeTypes[mediaType] || 'audio/mpeg',
      }],
      ...(isVideo ? {} : { audioOnlyMode: true, height: 50 }),
    })

    player.on('timeupdate', () => {
      setCurrentTime(Math.floor(player.currentTime()! * 1000))
    })

    playerRef.current = player
    return () => {
      player.dispose()
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current)
    }
  }, [fileId, mediaType, isVideo, mediaUrl, setCurrentTime])

  // Generate and update captions track reactively from store data
  const vttContent = useMemo(() => {
    if (!isVideo || !transcriptionResult?.utterances?.length) return null
    return generateVtt(transcriptionResult.utterances, speakerMappings)
  }, [isVideo, transcriptionResult?.utterances, speakerMappings])

  useEffect(() => {
    const player = playerRef.current
    if (!player || !isVideo || !vttContent) return

    // Remove old track
    if (trackRef.current) {
      player.removeRemoteTextTrack(trackRef.current as unknown as ReturnType<typeof player.addRemoteTextTrack>)
      trackRef.current = null
    }
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current)
      blobUrlRef.current = null
    }

    // Create new blob URL and track
    const blob = new Blob([vttContent], { type: 'text/vtt' })
    const url = URL.createObjectURL(blob)
    blobUrlRef.current = url

    const trackEl = player.addRemoteTextTrack({
      kind: 'captions',
      srclang: 'auto',
      label: 'Subtitles',
      src: url,
      default: false,
    }, false)

    trackRef.current = trackEl as unknown as HTMLTrackElement
  }, [vttContent, isVideo])

  useEffect(() => {
    if (seekTo !== null && playerRef.current) {
      playerRef.current.currentTime(seekTo / 1000)
      setSeekTo(null)
    }
  }, [seekTo, setSeekTo])

  const handleDownload = () => {
    const a = document.createElement('a')
    a.href = mediaUrl
    a.download = ''
    a.click()
  }

  return (
    <div className={`mx-6 my-2 ${isVideo ? 'flex flex-col items-center' : 'max-h-16'}`}>
      <div data-vjs-player className={isVideo ? 'w-full max-w-3xl' : ''}>
        <video ref={videoRef} className="video-js vjs-theme-city" />
      </div>
      <button
        onClick={handleDownload}
        className="mt-2 px-3 py-1 text-sm text-gray-400 hover:text-white transition-colors"
      >
        {t('player.download')}
      </button>
    </div>
  )
}
