/**
 * Money Contract - Single source of truth for monetary values
 *
 * Backend uses paise (integer). Frontend displays rupees.
 * This contract ensures consistent handling across the frontend.
 */

import { z } from 'zod'

/**
 * Money schema matching backend MoneyDTO
 * All monetary values in the system are represented as integer paise.
 */
export const MoneySchema = z.object({
  paise: z.number().int(),
  rupees: z.number(),
})

export type Money = z.infer<typeof MoneySchema>