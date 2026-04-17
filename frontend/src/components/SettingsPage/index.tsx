import { ApiTokensSection } from './ApiTokensSection'

export function SettingsPage() {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold text-white">Settings</h1>
      <ApiTokensSection />
    </div>
  )
}
