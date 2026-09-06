export default function ThemeToggle({ theme, onToggle }) {
  return <button className="icon-button" type="button" onClick={onToggle} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`} title="Toggle theme">{theme === 'dark' ? '☼' : '◐'}</button>
}
