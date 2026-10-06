import { useState } from 'react'
import {
  startInvestigation,
  useInvestigationEvents,
  useInvestigations,
} from '../data/useInvestigations'
import { capabilityActionDisabled } from '../capabilities/presentation.js'
import InvestigationResults from './InvestigationResults'

export default function InvestigationsPanel() {
  const { response, loading, error, refresh } = useInvestigations()
  const [kind, setKind] = useState<'event' | 'watch_event'>('event')
  const [triggerId, setTriggerId] = useState('')
  const [perspective, setPerspective] = useState<'system_observation' | 'public_information'>(
    'system_observation'
  )
  const [asOf, setAsOf] = useState(() => new Date().toISOString())
  const [steps, setSteps] = useState(8)
  const [elapsedMs, setElapsedMs] = useState(10000)
  const [activeOnly, setActiveOnly] = useState(false)
  const [pending, setPending] = useState(false)
  const [requestError, setRequestError] = useState<string | null>(null)
  const events = useInvestigationEvents(
    Date.parse(asOf),
    kind === 'watch_event' ? 'system_observation' : perspective
  )
  const disabled =
    capabilityActionDisabled(response?.capability ?? null, pending) || triggerId.trim() === ''

  async function start(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (disabled) return
    setPending(true)
    setRequestError(null)
    try {
      const cutoff = Date.parse(asOf)
      if (!Number.isFinite(cutoff) || !/(Z|[+-]\d{2}:\d{2})$/.test(asOf))
        throw new Error('As-Of must be an ISO instant with an explicit timezone offset.')
      await startInvestigation({
        trigger: { kind, id: triggerId.trim(), activeOnly: kind === 'watch_event' && activeOnly },
        boundary: {
          perspective: kind === 'watch_event' ? 'system_observation' : perspective,
          asOf: cutoff,
        },
        budgets: { steps, elapsedMs },
      })
    } catch (failure) {
      setRequestError(failure instanceof Error ? failure.message : 'Unable to run investigation')
    } finally {
      setPending(false)
      refresh()
    }
  }

  const inputClass = 'ml-2 rounded border border-[#2a2a2e] bg-[#0e0e10] p-1 text-xs text-[#f0f0f0]'
  return (
    <section className="mb-5 space-y-3 rounded-md border border-[#2a2a2e] bg-[#17171a] p-4 text-xs text-[#8b8b98]">
      <h2 className="m-0 text-sm text-[#f0f0f0]">Bounded investigations</h2>
      <p>
        Start from an explicit retained Event or Watch Event. Evidence, As-Of and capabilities
        freeze at creation. Core execution uses no model.
      </p>
      <form onSubmit={start} className="flex flex-wrap items-center gap-3">
        <label>
          Trigger
          <select
            value={kind}
            onChange={event => setKind(event.target.value as typeof kind)}
            className={inputClass}
          >
            <option value="event">Event</option>
            <option value="watch_event">Watch Event</option>
          </select>
        </label>
        <label>
          ID{' '}
          <input
            list={kind === 'event' ? 'investigation-event-ids' : undefined}
            required
            value={triggerId}
            onChange={event => setTriggerId(event.target.value)}
            className={inputClass}
          />
        </label>
        <datalist id="investigation-event-ids">
          {events.map(event => (
            <option key={event.id} value={event.id} />
          ))}
        </datalist>
        {kind === 'event' && (
          <label>
            Perspective
            <select
              value={perspective}
              onChange={event => setPerspective(event.target.value as typeof perspective)}
              className={inputClass}
            >
              <option value="system_observation">System observation</option>
              <option value="public_information">Public information</option>
            </select>
          </label>
        )}
        <label>
          As-Of{' '}
          <input
            required
            value={asOf}
            onChange={event => setAsOf(event.target.value)}
            className={`${inputClass} w-60`}
          />
        </label>
        <label>
          Steps{' '}
          <input
            type="number"
            required
            min={0}
            step={1}
            value={steps}
            onChange={event => setSteps(Number(event.target.value))}
            className={`${inputClass} w-16`}
          />
        </label>
        <label>
          Elapsed ms{' '}
          <input
            type="number"
            required
            min={0}
            step={1}
            value={elapsedMs}
            onChange={event => setElapsedMs(Number(event.target.value))}
            className={`${inputClass} w-24`}
          />
        </label>
        {kind === 'watch_event' && (
          <label>
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={event => setActiveOnly(event.target.checked)}
            />{' '}
            Require current active authorization
          </label>
        )}
        <button
          type="submit"
          disabled={disabled}
          className="rounded border border-[#2a2a2e] bg-transparent p-2 disabled:opacity-50"
        >
          {pending ? 'Running…' : 'Run investigation'}
        </button>
      </form>
      {loading && <p>Loading investigation runs…</p>}
      {(error || requestError) && <p className="text-[#e5534b]">{requestError ?? error}</p>}
      {response && <InvestigationResults response={response} />}
    </section>
  )
}
