import { useEffect, useState, type FormEvent } from 'react'
import {
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useSearchParams,
} from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ApiError,
  completePayment,
  getCurrentUser,
  getInventory,
  joinWaitlist,
  login,
  logout,
  reservePair,
} from './api'
import { useCheckout } from './useCheckout'
import './App.css'

const holdDurationSeconds = 5 * 60

function useCountdown(expiresAt?: string) {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    if (!expiresAt) return

    const timer = window.setInterval(() => setNow(Date.now()), 1_000)
    return () => window.clearInterval(timer)
  }, [expiresAt])

  return expiresAt
    ? Math.max(0, Math.ceil((new Date(expiresAt).getTime() - now) / 1_000))
    : 0
}

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

function Header() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { hold } = useCheckout()
  const { data: user } = useQuery({
    queryKey: ['current-user'],
    queryFn: getCurrentUser,
    retry: false,
  })
  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(['current-user'], null)
      navigate('/')
    },
  })

  return (
    <header className="site-header">
      <Link className="wordmark" to="/">
        SNEAK<span>DROP</span>
      </Link>

      <nav className="navigation" aria-label="Main navigation">
        <Link to="/">Stock</Link>
        <Link to="/cart" className={hold ? 'cart-link has-item' : 'cart-link'}>
          Cart{hold ? ' (1)' : ''}
        </Link>
        {user ? (
          <button
            className="text-button"
            type="button"
            onClick={() => logoutMutation.mutate()}
            disabled={logoutMutation.isPending}
          >
            Sign out
          </button>
        ) : (
          <Link className="login-link" to="/login">Sign in</Link>
        )}
      </nav>
    </header>
  )
}

function ProductVisual() {
  return (
    <div className="product-visual" aria-label="SneakDrop First Edition sneaker illustration" role="img">
      <span className="visual-label">SD<br />01</span>
      <span className="visual-stripe" />
      <span className="visual-sole" />
    </div>
  )
}

function StockPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { setHold } = useCheckout()
  const [message, setMessage] = useState('')
  const { data: user } = useQuery({
    queryKey: ['current-user'],
    queryFn: getCurrentUser,
    retry: false,
  })
  const inventoryQuery = useQuery({
    queryKey: ['inventory'],
    queryFn: getInventory,
    refetchInterval: 15_000,
  })

  const reserveMutation = useMutation({
    mutationFn: reservePair,
    onSuccess: (result) => {
      setHold(result.hold)
      void queryClient.invalidateQueries({ queryKey: ['inventory'] })
      navigate('/cart')
    },
    onError: (error) => {
      if (error instanceof ApiError && error.data.hold) {
        setHold(error.data.hold)
        navigate('/cart')
        return
      }
      setMessage(error instanceof Error ? error.message : 'Unable to reserve a pair.')
    },
  })

  const waitlistMutation = useMutation({
    mutationFn: joinWaitlist,
    onSuccess: (result) => {
      setMessage(`You are on the waitlist at position ${result.position}.`)
      void queryClient.invalidateQueries({ queryKey: ['inventory'] })
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : 'Unable to join the waitlist.')
    },
  })

  const inventory = inventoryQuery.data
  const isSoldOut = inventory?.sold_out ?? false

  function requireLogin(action: () => void) {
    setMessage('')
    if (!user) {
      navigate('/login?next=/')
      return
    }
    action()
  }

  return (
    <section className="stock-page page-content">
      <div className="product-panel">
        <ProductVisual />
        <p className="product-code">FIRST EDITION / DROP 001</p>
      </div>

      <div className="stock-copy">
        <p className="eyebrow">LIMITED RELEASE</p>
        <h1>SneakDrop<br />First Edition</h1>
        <p className="description">
          One product, twenty pairs. Reserve a pair for five minutes, then
          complete payment before your timer ends.
        </p>

        <div className="stock-card" aria-live="polite">
          <div>
            <p className="card-label">LIVE STOCK</p>
            {inventoryQuery.isPending ? (
              <strong>Checking availability...</strong>
            ) : inventoryQuery.isError ? (
              <strong className="status-error">Inventory unavailable</strong>
            ) : (
              <strong className={isSoldOut ? 'status-error' : 'status-success'}>
                {isSoldOut
                  ? 'Sold out'
                  : `${inventory?.available_stock} of ${inventory?.total_stock} pairs available`}
              </strong>
            )}
          </div>
          <button
            className="icon-button"
            type="button"
            onClick={() => void inventoryQuery.refetch()}
            disabled={inventoryQuery.isFetching}
          >
            {inventoryQuery.isFetching ? 'Updating' : 'Refresh'}
          </button>
        </div>

        {inventory?.waitlist_count ? (
          <p className="muted-note">{inventory.waitlist_count} customer(s) currently waiting.</p>
        ) : null}

        {message ? <p className="message" role="status">{message}</p> : null}

        <button
          className="primary-button"
          type="button"
          disabled={reserveMutation.isPending || waitlistMutation.isPending || inventoryQuery.isPending}
          onClick={() => requireLogin(() => {
            if (isSoldOut) {
              waitlistMutation.mutate()
            } else {
              reserveMutation.mutate()
            }
          })}
        >
          {reserveMutation.isPending || waitlistMutation.isPending
            ? 'Please wait...'
            : isSoldOut
              ? 'Join waitlist'
              : 'Reserve one pair'}
        </button>
        <p className="button-note">You must sign in before reserving.</p>
      </div>
    </section>
  )
}

function CartPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { hold, clearHold } = useCheckout()
  const remaining = useCountdown(hold?.expires_at)
  const expired = Boolean(hold) && remaining === 0

  useEffect(() => {
    if (expired) {
      void queryClient.invalidateQueries({ queryKey: ['inventory'] })
    }
  }, [expired, queryClient])

  if (!hold) {
    return (
      <section className="empty-page page-content">
        <p className="eyebrow">YOUR CART</p>
        <h1>Your cart is empty.</h1>
        <p>Reserve a pair from the stock page to start the five-minute checkout window.</p>
        <Link className="primary-button inline-button" to="/">View stock</Link>
      </section>
    )
  }

  return (
    <section className="checkout-page page-content">
      <div className="checkout-heading">
        <p className="eyebrow">YOUR CART</p>
        <h1>{expired ? 'Reservation expired' : 'Pair reserved'}</h1>
        <p>
          {expired
            ? 'This pair has been released back to stock. Reserve again to continue.'
            : 'Complete payment before the reservation timer reaches zero.'}
        </p>
      </div>

      <div className="cart-layout">
        <article className="cart-item">
          <div className="mini-product">SD<br />01</div>
          <div>
            <h2>SneakDrop First Edition</h2>
            <p>Quantity: 1 pair</p>
            <p>Reservation #{hold.hold_id}</p>
          </div>
          <strong>Limited</strong>
        </article>

        <aside className={expired ? 'timer-card timer-expired' : 'timer-card'}>
          <p className="card-label">RESERVATION TIMER</p>
          <div className="timer" aria-label={`${remaining} seconds remaining`}>
            {formatTime(remaining)}
          </div>
          <div className="timer-track" aria-hidden="true">
            <span style={{ width: `${(remaining / holdDurationSeconds) * 100}%` }} />
          </div>
          <p>{expired ? 'Your hold has ended.' : 'Your pair is protected while the timer runs.'}</p>

          {expired ? (
            <button className="secondary-button" type="button" onClick={() => {
              clearHold()
              navigate('/')
            }}>
              Back to stock
            </button>
          ) : (
            <Link className="primary-button inline-button" to="/payment">Continue to payment</Link>
          )}
        </aside>
      </div>
    </section>
  )
}

function PaymentPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { hold, setPayment } = useCheckout()
  const [cardNumber, setCardNumber] = useState('')
  const [error, setError] = useState('')
  const remaining = useCountdown(hold?.expires_at)
  const paymentMutation = useMutation({
    mutationFn: () => completePayment(hold!.hold_id),
    onSuccess: (result) => {
      setPayment(result)
      void queryClient.invalidateQueries({ queryKey: ['inventory'] })
      navigate('/success')
    },
    onError: (requestError) => {
      setError(requestError instanceof Error ? requestError.message : 'Payment could not be completed.')
    },
  })

  if (!hold) {
    return <Navigate to="/cart" replace />
  }

  if (remaining === 0) {
    return <Navigate to="/cart" replace />
  }

  function submitPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const digits = cardNumber.replace(/\s/g, '')

    if (digits.length < 12) {
      setError('Enter a valid card number to continue.')
      return
    }

    setError('')
    paymentMutation.mutate()
  }

  return (
    <section className="payment-page page-content">
      <div className="payment-copy">
        <p className="eyebrow">PAYMENT</p>
        <h1>Complete checkout</h1>
        <p>Demo checkout only. Card details are never sent or stored.</p>
        <p className="payment-timer">{formatTime(remaining)} remaining on your reservation</p>
      </div>

      <form className="payment-form" onSubmit={submitPayment}>
        <label htmlFor="card-name">
          Name on card
          <input id="card-name" autoComplete="cc-name" placeholder="Alex Johnson" required />
        </label>
        <label htmlFor="card-number">
          Card number
          <input
            id="card-number"
            inputMode="numeric"
            autoComplete="cc-number"
            placeholder="4242 4242 4242 4242"
            value={cardNumber}
            onChange={(event) => setCardNumber(event.target.value)}
            required
          />
        </label>
        <div className="input-row">
          <label htmlFor="expiry">
            Expiry
            <input id="expiry" inputMode="numeric" placeholder="12/30" required />
          </label>
          <label htmlFor="cvc">
            CVC
            <input id="cvc" inputMode="numeric" placeholder="123" required />
          </label>
        </div>
        {error ? <p className="message payment-error">{error}</p> : null}
        <button className="primary-button" type="submit" disabled={paymentMutation.isPending}>
          {paymentMutation.isPending ? 'Processing payment...' : 'Pay and confirm order'}
        </button>
      </form>
    </section>
  )
}

function SuccessPage() {
  const { payment } = useCheckout()

  if (!payment) {
    return <Navigate to="/" replace />
  }

  const isSuccess = payment.outcome === 'processed'

  return (
    <section className="success-page page-content">
      <p className="eyebrow">{isSuccess ? 'ORDER CONFIRMED' : 'PAYMENT UPDATE'}</p>
      <h1>{isSuccess ? 'You got the drop.' : 'Payment arrived too late.'}</h1>
      <p>
        {isSuccess
          ? `Order #${payment.order_id} is confirmed. Your SneakDrop First Edition pair is yours.`
          : 'Your reservation was already released, so no order was created.'}
      </p>
      <Link className="primary-button inline-button" to="/">Return to stock</Link>
    </section>
  )
}

function LoginPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const loginMutation = useMutation({
    mutationFn: () => login(username, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['current-user'], user)
      const next = searchParams.get('next')
      navigate(next?.startsWith('/') ? next : '/')
    },
    onError: (requestError) => {
      setError(requestError instanceof Error ? requestError.message : 'Unable to sign in.')
    },
  })

  function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    loginMutation.mutate()
  }

  return (
    <section className="login-page page-content">
      <div>
        <p className="eyebrow">CUSTOMER ACCESS</p>
        <h1>Sign in to reserve.</h1>
        <p>Use a Django user created through the admin panel. Your session stays in this browser only.</p>
      </div>

      <form className="login-form" onSubmit={submitLogin}>
        <label htmlFor="username">
          Username
          <input
            id="username"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label htmlFor="password">
          Password
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error ? <p className="message payment-error">{error}</p> : null}
        <button className="primary-button" type="submit" disabled={loginMutation.isPending}>
          {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </section>
  )
}

function App() {
  const location = useLocation()

  return (
    <main className="app-shell">
      <Header />
      <Routes location={location}>
        <Route path="/" element={<StockPage />} />
        <Route path="/cart" element={<CartPage />} />
        <Route path="/payment" element={<PaymentPage />} />
        <Route path="/success" element={<SuccessPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  )
}

export default App
