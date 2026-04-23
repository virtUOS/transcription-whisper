import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../api/client'

interface Props {
  token: string
}

export function InviteLanding({ token }: Props) {
  const { t } = useTranslation()
  const [status, setStatus] = useState<'loading' | 'redirecting' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    let cancelled = false
    async function run() {
      try {
        const { redirect_url } = await api.acceptInvitation(token)
        if (cancelled) return
        setStatus('redirecting')
        window.location.href = redirect_url
      } catch (err) {
        if (cancelled) return
        setStatus('error')
        setMessage(err instanceof Error ? err.message : 'Failed')
      }
    }
    void run()
    return () => { cancelled = true }
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-neutral-950">
      <div className="max-w-md w-full bg-neutral-900 rounded-lg p-6 text-center">
        {status === 'loading' && <p className="text-white">{t('invite.verifying')}</p>}
        {status === 'redirecting' && <p className="text-white">{t('invite.redirecting')}</p>}
        {status === 'error' && (
          <>
            <p className="text-red-400 font-semibold mb-2">{t('invite.error_title')}</p>
            <p className="text-neutral-300 text-sm">{message}</p>
          </>
        )}
      </div>
    </div>
  )
}
