import { useEffect, useState, type ReactNode } from 'react'
import type { Hold, PaymentResult } from './api'
import { CheckoutContext, type CheckoutContextValue } from './checkout-context'

type CheckoutState = {
  hold: Hold | null
  payment: PaymentResult | null
}

const storageKey = 'sneakdrop-checkout'

function readStoredCheckout(): CheckoutState {
  try {
    const value = sessionStorage.getItem(storageKey)
    return value ? (JSON.parse(value) as CheckoutState) : { hold: null, payment: null }
  } catch {
    return { hold: null, payment: null }
  }
}

export function CheckoutProvider({ children }: { children: ReactNode }) {
  const [checkout, setCheckout] = useState<CheckoutState>(readStoredCheckout)

  useEffect(() => {
    sessionStorage.setItem(storageKey, JSON.stringify(checkout))
  }, [checkout])

  const value: CheckoutContextValue = {
    ...checkout,
    setHold: (hold) => setCheckout((current) => ({ ...current, hold })),
    clearHold: () => setCheckout((current) => ({ ...current, hold: null })),
    setPayment: (payment) => setCheckout({ hold: null, payment }),
  }

  return <CheckoutContext.Provider value={value}>{children}</CheckoutContext.Provider>
}
