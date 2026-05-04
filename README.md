# Nodepad #

Nodepad is a powerful, hierarchical outliner application designed for creating and managing nested lists with ease. It is inspired by modern outliner apps like Dynalist, Workflowy, and Checkvist.

**Current Version:** v.0.4 beta  
**Status:** In active development. Online demo will be deployed soon.

---

## Project Links (Local Development)

- **Frontend:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Adminer (Database Tool):** [http://localhost:8080](http://localhost:8080)
- **Mailcatcher:** [http://localhost:1080](http://localhost:1080)

---

## Development Workflow

### Docker Compose Watch

This project uses Docker Compose's native `watch` feature for a seamless development experience. It automatically syncs changes to the containers and rebuilds them when necessary.

To start development with watch mode:
```bash
docker compose watch
```

Alternatively, you can run:
```bash
docker compose up --build
```

### Keyboard Shortcuts

Nodepad is designed to be keyboard-first. Use these shortcuts in the list editing screen:

| Shortcut | Action |
| :--- | :--- |
| **Enter** | Save and finish editing |
| **Shift + Enter** | Create a new child node |
| **Tab** | Indent node (move right) |
| **Shift + Tab** | Outdent node (move left) |
| **↑ / ↓ Arrows** | Navigate between nodes |
| **Backspace** | Delete empty node (when empty) |
| **Ctrl + Z** | Undo last node edit/delete |
| **Escape** | Cancel editing |

---

## Disclaimer #

This project is a practice application created to improve my skills in frontend and backend development. It is **not an official product**. All design elements and content are original or freely available for use.
