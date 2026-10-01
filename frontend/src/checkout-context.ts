import { createContext } from 'react'
import type { Hold, PaymentResult } from './api'

export type CheckoutContextValue = {
  hold: Hold | null
  payment: PaymentResult | null
  setHold: (hold: Hold) => void
  clearHold: () => void
  setPayment: (payment: PaymentResult) => void
}

export const CheckoutContext = createContext<CheckoutContextValue | null>(null)
