import { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../api/client'
import { useStore } from '../../store'

export function FileUpload() {
  const { t } = useTranslation()
  const file = useStore((s) => s.file)
  const setFile = useStore((s) => s.setFile)
  const reset = useStore((s) => s.reset)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = useCallback(async (selectedFile: File) => {
    setUploading(true)
    setError(null)
    try {
      const fileInfo = await api.uploadFile(selectedFile)
      setFile(fileInfo)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [setFile])

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
      <div className="flex items-center gap-4 px-6 py-2 bg-gray-800 border-b border-gray-700 text-sm text-gray-300">
        <span>{file.original_filename}</span>
        <span className="text-gray-500">({(file.file_size / 1024 / 1024).toFixed(1)} MB)</span>
        <button onClick={() => reset()} className="text-red-400 hover:text-red-300">
          {t('upload.deleteFile')}
        </button>
      </div>
    )
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className="mx-6 my-4 p-8 border-2 border-dashed border-gray-600 rounded-lg text-center hover:border-blue-500 transition-colors cursor-pointer"
    >
      <input type="file" accept=".mp3,.wav,.mp4" onChange={handleFileInput} className="hidden" id="file-upload" disabled={uploading} />
      <label htmlFor="file-upload" className="cursor-pointer">
        <p className="text-gray-300">{uploading ? t('common.loading') : t('upload.dragDrop')}</p>
        <p className="text-gray-500 text-sm mt-2">{t('upload.supportedFormats')}</p>
      </label>
      {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
    </div>
  )
}
