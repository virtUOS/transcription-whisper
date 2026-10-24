import type { TFunction } from 'i18next'
import type { LeaveReason } from '../store'

export function leaveMessages(t: TFunction): Record<LeaveReason, string> {
  return {
    upload: t('upload.confirmLeave'),
    recording: t('recorder.confirmLeave'),
    unsavedEdits: t('editor.confirmLeave'),
  }
}
