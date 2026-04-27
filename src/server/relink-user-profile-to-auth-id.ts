import { randomUUID } from 'crypto'
import type { TransactionSql } from 'postgres'

export type RelinkUserProfileParams = {
  legacyUserId: string
  newUserId: string
  normalizedEmail: string
  fullName: string
}

/**
 * When Neon Auth issues a new `user.id` for the same email, `user_profiles` still
 * references the old UUID. Move the row and repoint all known FKs in one transaction.
 */
export async function relinkUserProfileToAuthIdInTx(
  tx: TransactionSql,
  p: RelinkUserProfileParams
): Promise<void> {
  const { legacyUserId, newUserId, normalizedEmail, fullName } = p
  const scratchEmail = `legacy-${randomUUID()}@accountuitive-profile-relink.invalid`

  await tx`
    UPDATE public.user_profiles
    SET email = ${scratchEmail}
    WHERE id = ${legacyUserId}::uuid
  `

  await tx`
    INSERT INTO public.user_profiles (
      id, email, full_name, avatar_url, phone, is_super_admin, preferences, last_sign_in_at,
      created_at, updated_at
    )
    SELECT
      ${newUserId}::uuid,
      ${normalizedEmail},
      ${fullName},
      avatar_url,
      phone,
      is_super_admin,
      preferences,
      last_sign_in_at,
      created_at,
      updated_at
    FROM public.user_profiles
    WHERE id = ${legacyUserId}::uuid
  `

  await tx`
    UPDATE public.organization_members
    SET user_id = ${newUserId}::uuid
    WHERE user_id = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.organization_members
    SET invited_by = ${newUserId}::uuid
    WHERE invited_by = ${legacyUserId}::uuid
  `

  await tx`
    UPDATE public.accounts SET created_by = ${newUserId}::uuid WHERE created_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.journal_entries SET created_by = ${newUserId}::uuid WHERE created_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.journal_entries SET posted_by = ${newUserId}::uuid WHERE posted_by = ${legacyUserId}::uuid
  `

  await tx`
    UPDATE public.inventory_categories SET created_by = ${newUserId}::uuid WHERE created_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.inventory_items SET created_by = ${newUserId}::uuid WHERE created_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.inventory_transactions SET created_by = ${newUserId}::uuid WHERE created_by = ${legacyUserId}::uuid
  `

  await tx`
    UPDATE public.inventory_vouchers SET requested_by = ${newUserId}::uuid WHERE requested_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.inventory_vouchers SET finance_approved_by = ${newUserId}::uuid WHERE finance_approved_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.inventory_vouchers SET rejected_by = ${newUserId}::uuid WHERE rejected_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.inventory_vouchers SET executed_by = ${newUserId}::uuid WHERE executed_by = ${legacyUserId}::uuid
  `

  await tx`
    UPDATE public.voucher_attachments SET uploaded_by = ${newUserId}::uuid WHERE uploaded_by = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.voucher_approvals SET approver_id = ${newUserId}::uuid WHERE approver_id = ${legacyUserId}::uuid
  `
  await tx`
    UPDATE public.voucher_expiration_log SET renewed_by = ${newUserId}::uuid WHERE renewed_by = ${legacyUserId}::uuid
  `

  await tx`DELETE FROM public.user_profiles WHERE id = ${legacyUserId}::uuid`
}
