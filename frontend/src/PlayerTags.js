
import { Box } from '@mui/material';
import TagChip from './TagChip';

export default function PlayerTags({ player, onTagClick }) {
  if (!player.tags || !player.tags.length) return null;

  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1, width: '100%' }}>
      {player.tags.map(tag => (
        <TagChip
          key={`player-${player.id}-tag-${tag.id}`}
          tag={tag}
          onClick={onTagClick ? (e => { e.preventDefault(); e.stopPropagation(); onTagClick(tag); }) : undefined}
        />
      ))}
    </Box>
  );
}
