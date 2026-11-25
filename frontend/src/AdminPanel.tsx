import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

type Session = { configured: boolean; authenticated: boolean }

async function readSession(response: Response): Promise<Session> {
  if (!response.ok) throw new Error('Session request failed')
  const result: unknown = await response.json()
  if (
    typeof result !== 'object' || result === null ||
    !('configured' in result) || typeof result.configured !== 'boolean' ||
    !('authenticated' in result) || typeof result.authenticated !== 'boolean'
  ) {
    throw new Error('Invalid session response')
  }
  return { configured: result.configured, authenticated: result.authenticated }
}

const sessionUrl = '/api/admin/session'

export default function AdminPanel() {
  const [session, setSession] = useState<Session | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(5000)])

    async function loadSession() {
      try {
        const nextSession = await readSession(await fetch(sessionUrl, { signal, cache: 'no-store' }))
        if (!controller.signal.aborted) setSession(nextSession)
      } catch {
        if (!controller.signal.aborted) setError('Không thể kiểm tra phiên Admin.')
      }
    }

    void loadSession()
    return () => controller.abort()
  }, [attempt])

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const password = new FormData(form).get('password')
    setPending(true)
    setError('')
    try {
      const response = await fetch(sessionUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
        signal: AbortSignal.timeout(10000),
      })
      if (response.status === 401) {
        setError('Mật khẩu không đúng. Vui lòng nhập lại.')
        return
      }
      if (response.status === 409) {
        setSession({ configured: false, authenticated: false })
        return
      }
      setSession(await readSession(response))
      form.reset()
    } catch {
      setError('Không thể đăng nhập. Hãy thử lại.')
    } finally {
      setPending(false)
    }
  }

  async function signOut() {
    setPending(true)
    setError('')
    try {
      const response = await fetch(sessionUrl, { method: 'DELETE', signal: AbortSignal.timeout(5000) })
      if (!response.ok) throw new Error('Logout failed')
      setSession({ configured: true, authenticated: false })
    } catch {
      setError('Không thể đăng xuất. Hãy thử lại.')
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="panel admin-panel" aria-labelledby="admin-title">
      <h2 id="admin-title">{session?.authenticated ? 'Tài khoản Admin' : 'Đăng nhập Admin'}</h2>
      {error && <p className="form-error" role="alert">{error}</p>}
      {session === null && (
        error ? (
          <button type="button" onClick={() => {
            setError('')
            setAttempt((value) => value + 1)
          }}>Kiểm tra phiên</button>
        ) : <p role="status">Đang kiểm tra phiên…</p>
      )}
      {session && !session.configured && (
        <p>Chưa đặt mật khẩu Admin. Chạy <code>python -m backend.set_admin_password</code> bằng Python trong môi trường <code>.venv</code>, rồi tải lại trang.</p>
      )}
      {session?.authenticated && (
        <>
          <p role="status">Bạn đã đăng nhập.</p>
          <button type="button" disabled={pending} onClick={signOut}>
            {pending ? 'Đang đăng xuất…' : 'Đăng xuất'}
          </button>
        </>
      )}
      {session?.configured && !session.authenticated && (
        <form onSubmit={signIn}>
          <label htmlFor="admin-password">Mật khẩu</label>
          <input id="admin-password" name="password" type="password" autoComplete="current-password"
            required disabled={pending} />
          <button type="submit" disabled={pending}>{pending ? 'Đang đăng nhập…' : 'Đăng nhập'}</button>
        </form>
      )}
    </section>
  )
}
