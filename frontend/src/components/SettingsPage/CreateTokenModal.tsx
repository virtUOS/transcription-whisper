import { useState } from 'react'
import { api } from '../../api/client'
import type { ApiTokenCreated } from '../../api/types'

interface Props {
  onClose: () => void
  onCreated: () => void
}

const EXPIRY_OPTIONS: { label: string; days: number | null }[] = [
  { label: '30 days', days: 30 },
  { label: '90 days', days: 90 },
  { label: '365 days', days: 365 },
  { label: 'Never', days: null },
]

export function CreateTokenModal({ onClose, onCreated }: Props) {
  const [name, setName] = useState('')
  const [expiryDays, setExpiryDays] = useState<number | null>(90)
  const [created, setCreated] = useState<ApiTokenCreated | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

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
            <h2 className="text-lg font-semibold text-white">Token created</h2>
            <p className="text-sm text-yellow-400">
              Save this now — you won't see it again.
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
                Copy
              </button>
              <button
                type="button"
                onClick={handleDone}
                className="text-sm bg-blue-600 hover:bg-blue-500 text-white rounded px-4 py-1.5"
              >
                Done
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 className="text-lg font-semibold text-white">Create API token</h2>

            {error && (
              <p className="text-sm text-red-400">{error}</p>
            )}

            <div>
              <label className="block text-xs text-gray-400 mb-1">Name</label>
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
              <label htmlFor="token-expiry-select" className="block text-xs text-gray-400 mb-1">Expires in</label>
              <select
                id="token-expiry-select"
                value={expiryDays === null ? '' : String(expiryDays)}
                onChange={(e) => setExpiryDays(e.target.value === '' ? null : Number(e.target.value))}
                className="w-full bg-gray-800 text-white text-sm rounded px-3 py-1.5 outline-none focus:ring-1 focus:ring-blue-500 border border-gray-700"
              >
                {EXPIRY_OPTIONS.map((opt) => (
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
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreate}
                disabled={submitting || !name.trim()}
                className="text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded px-4 py-1.5"
              >
                {submitting ? '…' : 'Create'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
