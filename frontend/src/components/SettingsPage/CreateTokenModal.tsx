import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../api/client'
import type { ApiTokenCreated } from '../../api/types'

interface Props {
  onClose: () => void
  onCreated: () => void
}

export function CreateTokenModal({ onClose, onCreated }: Props) {
  const { t } = useTranslation()
  const [name, setName] = useState('')
  const [expiryDays, setExpiryDays] = useState<number | null>(90)
  const [created, setCreated] = useState<ApiTokenCreated | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const expiryOptions = [
    { label: t('settings.apiTokens.expiry30'), days: 30 },
    { label: t('settings.apiTokens.expiry90'), days: 90 },
    { label: t('settings.apiTokens.expiry365'), days: 365 },
    { label: t('settings.apiTokens.expiryNever'), days: null },
  ]

  async function handleCreate() {
    setError(null)
    setSubmitting(true)
    try {
      const result = await api.createApiToken(name.trim(), expiryDays)
      setCreated(result)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCopy() {
    if (created) await navigator.clipboard.writeText(created.token)
  }

  function handleDone() {
    setCreated(null)
    onCreated()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-md w-full space-y-4 mx-4">
        {created ? (
          <>
            <h2 className="text-lg font-semibold text-white">{t('settings.apiTokens.createdHeader')}</h2>
            <p className="text-sm text-yellow-400">
              {t('settings.apiTokens.saveNowWarning')}
            </p>
            <div className="bg-gray-800 rounded px-3 py-2 font-mono text-sm text-green-400 break-all select-all">
              {created.token}
            </div>
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={handleCopy}
                className="text-sm bg-gray-700 hover:bg-gray-600 text-white rounded px-4 py-1.5"
              >
                {t('settings.apiTokens.copy')}
              </button>
              <button
                type="button"
                onClick={handleDone}
                className="text-sm bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-1.5"
              >
                {t('settings.apiTokens.done')}
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 className="text-lg font-semibold text-white">{t('settings.apiTokens.createButton')}</h2>

            {error && (
              <p className="text-sm text-red-400">{error}</p>
            )}

            <div>
              <label className="block text-xs text-gray-400 mb-1">{t('settings.apiTokens.nameLabel')}</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={64}
                placeholder="e.g. my-script"
                className="w-full bg-gray-800 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500 border border-gray-700"
              />
            </div>

            <div>
              <label htmlFor="token-expiry-select" className="block text-xs text-gray-400 mb-1">{t('settings.apiTokens.expiresLabel')}</label>
              <select
                id="token-expiry-select"
                value={expiryDays === null ? '' : String(expiryDays)}
                onChange={(e) => setExpiryDays(e.target.value === '' ? null : Number(e.target.value))}
                className="w-full bg-gray-800 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500 border border-gray-700"
              >
                {expiryOptions.map((opt) => (
                  <option key={opt.label} value={opt.days === null ? '' : String(opt.days)}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={onClose}
                className="text-sm text-gray-400 hover:text-white px-3 py-1.5"
              >
                {t('settings.apiTokens.cancel')}
              </button>
              <button
                type="button"
                onClick={handleCreate}
                disabled={submitting || !name.trim()}
                className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded px-4 py-1.5"
              >
                {submitting ? t('settings.apiTokens.prefixSuffix') : t('settings.apiTokens.createCta')}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
