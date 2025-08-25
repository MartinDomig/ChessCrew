// Utility to pick best contrast color (black or white) for a given background color
export function getContrastColor(bgColor) {
  if (!bgColor) return '#fff';
  const color = bgColor.charAt(0) === '#' ? bgColor.substring(1) : bgColor;
  let r, g, b;
  if (color.length === 3) {
    r = parseInt(color[0] + color[0], 16);
    g = parseInt(color[1] + color[1], 16);
    b = parseInt(color[2] + color[2], 16);
  } else if (color.length === 6) {
    r = parseInt(color.substring(0,2), 16);
    g = parseInt(color.substring(2,4), 16);
    b = parseInt(color.substring(4,6), 16);
  } else {
    return '#fff';
  }
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  return brightness > 180 ? '#222' : '#fff';
}
