import { config } from 'dotenv'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const rootEnvPath = join(here, '..', '..', '..', '.env')

config({ path: rootEnvPath })
