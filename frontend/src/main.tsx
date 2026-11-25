import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

type Health = { status: 'ok'; database: 'ready'; shop_name: string }
type Connection = { state: 'checking' | 'unavailable' } | { state: 'ready'; shop: string }

function App() {
  const [connection, setConnection] = useState<Connection>({ state: 'checking' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    async function checkHealth() {
      try {
        const response = await fetch('/api/health', { signal: controller.signal, cache: 'no-store' })
        if (!response.ok) throw new Error('Readiness check failed')
        const data: Health = await response.json()
        if (data.status !== 'ok' || data.database !== 'ready' || typeof data.shop_name !== 'string') {
          throw new Error('Invalid readiness response')
        }
        if (!controller.signal.aborted) setConnection({ state: 'ready', shop: data.shop_name })
      } catch {
        if (!controller.signal.aborted) setConnection({ state: 'unavailable' })
      }
    }

    void checkHealth()
    return () => controller.abort()
  }, [attempt])

  const status = {
    checking: 'Đang kiểm tra kết nối…',
    ready: 'Ứng dụng và cơ sở dữ liệu đã sẵn sàng.',
    unavailable: 'Ứng dụng hoặc cơ sở dữ liệu chưa sẵn sàng.',
  }[connection.state]

  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <span className="mark" aria-hidden="true">J</span>
          <span>June OMS</span>
        </div>
      </header>
      <main>
        <h1>Trạng thái hệ thống</h1>
        <section className="panel" aria-label="Kết nối local">
          <div role="status" className="status" data-state={connection.state}>
            <span className="dot" aria-hidden="true" />
            {status}
          </div>
          {connection.state === 'ready' && (
            <dl>
              <div><dt>Cửa hàng</dt><dd>{connection.shop}</dd></div>
              <div><dt>Cơ sở dữ liệu</dt><dd>SQLite</dd></div>
            </dl>
          )}
          <button
            type="button"
            disabled={connection.state === 'checking'}
            onClick={() => {
              setConnection({ state: 'checking' })
              setAttempt((value) => value + 1)
            }}
          >Kiểm tra lại</button>
        </section>
      </main>
    </>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
