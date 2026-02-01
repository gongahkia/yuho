import { Button } from "@/components/ui/button"

interface YuhoIDEToolbarProps {
  onRun: () => void
  onSave: () => void
}

export function YuhoIDEToolbar({ onRun, onSave }: YuhoIDEToolbarProps) {
  return (
    <div className="flex gap-2 mb-4">
      <Button onClick={onRun}>Run</Button>
      <Button onClick={onSave}>Save</Button>
    </div>
  )
}