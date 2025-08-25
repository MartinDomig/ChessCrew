import { Chip } from '@mui/material';
import { getContrastColor } from './colorUtils';

export default function TagChip({ tag, onClick }) {
  const bg = tag.color || undefined;
  const fg = getContrastColor(bg);
  return (
    <Chip
      label={tag.name}
      style={{
        backgroundColor: bg,
        color: fg,
        border: '1px solid rgba(0,0,0,0.2)'
      }}
      onClick={onClick}
    />
  );
}
