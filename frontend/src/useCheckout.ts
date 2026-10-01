import { useContext } from 'react'
import { CheckoutContext } from './checkout-context'

export function useCheckout() {
  const checkout = useContext(CheckoutContext)

  if (!checkout) {
    throw new Error('useCheckout must be used inside CheckoutProvider.')
  }

  return checkout
}
