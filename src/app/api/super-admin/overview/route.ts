import { NextResponse } from 'next/server'
import {
  getSuperAdminOverview,
  requirePlatformSuperAdmin,
  SuperAdminHttpError,
} from '@/server/super-admin'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    await requirePlatformSuperAdmin()
    const overview = await getSuperAdminOverview()
    return NextResponse.json(overview)
  } catch (e) {
    if (e instanceof SuperAdminHttpError) {
      return NextResponse.json({ error: e.message }, { status: e.status })
    }
    console.error('super admin overview GET', e)
    return NextResponse.json({ error: 'Failed to load super admin overview' }, { status: 500 })
  }
}
