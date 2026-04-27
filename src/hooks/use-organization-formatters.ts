'use client'

import { useCallback, useMemo } from 'react'
import { useCurrentOrganization } from '@/hooks/use-current-organization'
import { formatMonetaryAmount } from '@/lib/utils'
import { getOrganizationAccountingDisplay } from '@/lib/organization-settings-defaults'

/**
 * Money formatting and reporting currency for the **current** organization.
 * All members of the same org read the same `organizations.settings` row from the server.
 */
export function useOrganizationFormatters() {
  const organization = useCurrentOrganization()
  const { reportingCurrency, decimalPlaces } = useMemo(
    () => getOrganizationAccountingDisplay(organization),
    [organization]
  )

  const formatCurrency = useCallback(
    (amount: number) => formatMonetaryAmount(amount, reportingCurrency, decimalPlaces),
    [reportingCurrency, decimalPlaces]
  )

  return {
    organization,
    reportingCurrency,
    decimalPlaces,
    formatCurrency,
  }
}
