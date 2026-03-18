import { useEffect, useRef } from 'react'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'
import { useStore } from '../../store'

interface Props {
  fileId: string
  mediaType: string
}

export function MediaPlayer({ fileId, mediaType }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const playerRef = useRef<ReturnType<typeof videojs> | null>(null)
  const setCurrentTime = useStore((s) => s.setCurrentTime)
  const seekTo = useStore((s) => s.seekTo)
  const setSeekTo = useStore((s) => s.setSeekTo)

  const isVideo = mediaType === 'mp4'
  const mediaUrl = `/api/media/${fileId}`

  useEffect(() => {
    if (!videoRef.current) return

    const player = videojs(videoRef.current, {
      controls: true,
      responsive: true,
      fluid: !isVideo,
      sources: [{
        src: mediaUrl,
        type: isVideo ? 'video/mp4' : 'audio/mpeg',
      }],
      ...(isVideo ? {} : { audioOnlyMode: true, height: 50 }),
    })

    player.on('timeupdate', () => {
      setCurrentTime(Math.floor(player.currentTime()! * 1000))
    })

    playerRef.current = player
    return () => { player.dispose() }
  }, [fileId, mediaType, isVideo, mediaUrl, setCurrentTime])

  useEffect(() => {
    if (seekTo !== null && playerRef.current) {
      playerRef.current.currentTime(seekTo / 1000)
      setSeekTo(null)
    }
  }, [seekTo, setSeekTo])

  return (
    <div className={`mx-6 my-2 ${isVideo ? '' : 'max-h-16'}`}>
      <div data-vjs-player>
        <video ref={videoRef} className="video-js vjs-theme-city" />
      </div>
    </div>
  )
}
