import { useTranslation } from 'react-i18next'
import { useStore } from '../../store'
import { ApiTokensSection } from './ApiTokensSection'
import { InvitationsSection } from '../InvitationsSection'

export function SettingsPage() {
  const { t } = useTranslation()
  const config = useStore((s) => s.config)
  const isAdmin = config?.is_admin ?? false
  const invitationMode = config?.invitation_mode ?? false

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold text-white">{t('settings.title')}</h1>
      <ApiTokensSection />
      {isAdmin && invitationMode && <InvitationsSection />}
    </div>
  )
}
