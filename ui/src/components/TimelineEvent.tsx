import type { LiveEvent } from '../types/logs'

interface TimelineEventProps {
  event: LiveEvent
}

export default function TimelineEvent({ event }: TimelineEventProps) {
  const timestamp = new Date(event.ts).toLocaleTimeString('tr-TR', {
    hour12: false
  })

  return (
    <li className={`timeline-event level-${event.level}`}>
      <div className="timeline-head">
        <strong>{event.step}</strong>
        <span>{timestamp}</span>
      </div>
      <p>{event.message}</p>
    </li>
  )
}
