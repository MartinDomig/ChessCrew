import { Chip } from '@mui/material';
import { getContrastColor } from './colorUtils';

export default function TagChip({ tag, onClick, onDelete, size = 'medium' }) {
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
      onClick={onClick ? (e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick(tag);
      } : undefined}
      onDelete={onDelete ? () => { onDelete(tag); } : undefined}
      size={size}
    />
  );
}
