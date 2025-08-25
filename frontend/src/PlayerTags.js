
import { Box, Chip } from '@mui/material';
import { getContrastColor } from './colorUtils';

export default function PlayerTags({ player, onTagClick }) {
  if (!player.tags || !player.tags.length) return null;

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1, width: '100%' }}>
      {player.tags.map(tag => {
        const bg = tag.color || undefined;
        const fg = getContrastColor(bg);
        return (
          <Chip
            key={`player-${player.id}-tag-${tag.id}`}
            label={tag.name}
            style={{
              backgroundColor: bg,
              color: fg,
              border: '1px solid rgba(0,0,0,0.2)'
            }}
            onClick={onTagClick ? (e => { e.preventDefault(); e.stopPropagation(); onTagClick(tag); }) : undefined}
          />
        );
      })}
    </Box>
  );
}
