import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import { useStore } from '../../store'

interface Props {
  fileId: string
  mediaType: string
}

export function MediaPlayer({ fileId, mediaType }: Props) {
  const { t } = useTranslation()
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const playerRef = useRef<ReturnType<typeof videojs> | null>(null)
  const setCurrentTime = useStore((s) => s.setCurrentTime)
  const seekTo = useStore((s) => s.seekTo)
  const setSeekTo = useStore((s) => s.setSeekTo)
  const transcriptionId = useStore((s) => s.transcriptionId)

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

    // Add VTT subtitle track for video once player is ready
    if (isVideo && transcriptionId) {
      player.ready(() => {
        player.addRemoteTextTrack({
          kind: 'captions',
          srclang: 'auto',
          label: 'Subtitles',
          src: `/api/transcription/${transcriptionId}/export/vtt`,
          default: false,
        }, false)
      })
    }

    player.on('timeupdate', () => {
      setCurrentTime(Math.floor(player.currentTime()! * 1000))
    })

    playerRef.current = player
    return () => { player.dispose() }
  }, [fileId, mediaType, isVideo, mediaUrl, setCurrentTime, transcriptionId])

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
