import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../api/client'
import { useStore } from '../../store'
import { formatFileSize } from '../../utils/format'

const MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024 // 1GB

export function FileUpload() {
  const { t } = useTranslation()
  const file = useStore((s) => s.file)
  const setFile = useStore((s) => s.setFile)
  const transcriptionId = useStore((s) => s.transcriptionId)
  const transcriptionTitle = useStore((s) => s.transcriptionTitle)
  const reset = useStore((s) => s.reset)
  const uploading = useStore((s) => s.uploading)
  const setUploading = useStore((s) => s.setUploading)
  const setUploadAbortController = useStore((s) => s.setUploadAbortController)
  const [error, setError] = useState<string | null>(null)

  const setCurrentView = useStore((s) => s.setCurrentView)

  const handleDelete = useCallback(async () => {
    if (transcriptionId) {
      try {
        await api.deleteTranscription(transcriptionId)
      } catch (e) {
        console.error('Delete failed:', e)
      }
    }
    reset()
    setCurrentView('archive')
  }, [transcriptionId, reset, setCurrentView])

  const handleUpload = useCallback(async (selectedFile: File) => {
    setError(null)
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(t('upload.fileTooLarge'))
      return
    }
    const controller = new AbortController()
    setUploadAbortController(controller)
    setUploading(true)
    try {
      const fileInfo = await api.uploadFile(selectedFile, controller.signal)
      setFile(fileInfo)
    } catch (e) {
      // AbortError is a user-initiated cancel; don't show an error banner.
      if (e instanceof Error && e.name === 'AbortError') return
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
      setUploadAbortController(null)
    }
  }, [setFile, setUploading, setUploadAbortController, t])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) handleUpload(droppedFile)
  }, [handleUpload])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) handleUpload(selectedFile)
  }, [handleUpload])

  if (file) {
    return (
      <div className="flex items-center gap-4 px-6 py-2 bg-gray-800 border-b border-gray-700 text-sm text-gray-300 min-w-0">
        <span className="truncate min-w-0">
          {transcriptionTitle ? <>{transcriptionTitle} <span className="text-gray-500">[{file.original_filename}]</span></> : file.original_filename}
        </span>
        <span className="text-gray-500 shrink-0">({formatFileSize(file.file_size)})</span>
        <button onClick={handleDelete} className="text-red-400 hover:text-red-300 shrink-0">
          {t('upload.deleteFile')}
        </button>
      </div>
    )
  }

  return (
    <div
      onDrop={uploading ? undefined : handleDrop}
      onDragOver={uploading ? undefined : (e) => e.preventDefault()}
      className={`mx-6 my-4 p-8 border-2 border-dashed rounded-lg text-center transition-colors ${uploading ? 'border-gray-700 cursor-default' : 'border-gray-600 hover:border-blue-500 cursor-pointer'}`}
    >
      <input type="file" accept=".mp3,.wav,.mp4,.webm,.m4a,.mov,.aac,.opus,.ogg" onChange={handleFileInput} className="hidden" id="file-upload" disabled={uploading} />
      {uploading ? (
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
          <p className="text-gray-300">{t('transcription.statusUploading')}</p>
        </div>
      ) : (
        <label htmlFor="file-upload" className="cursor-pointer">
          <p className="text-gray-300">{t('upload.dragDrop')}</p>
          <p className="text-gray-500 text-sm mt-2">{t('upload.supportedFormats')}</p>
        </label>
      )}
      {error && (
        <div className="mt-3 p-4 bg-red-900/30 rounded-lg border border-red-700">
          <div className="flex items-center gap-3">
            <span className="text-red-400 text-lg" aria-hidden="true">!</span>
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        </div>
      )}
    </div>
  )
}
