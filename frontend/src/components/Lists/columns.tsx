import type { ColumnDef } from "@tanstack/react-table"

import type { NodeListPublic } from "@/client"
import { cn } from "@/lib/utils"
import { ListActionsMenu } from "./ListActionsMenu"

export const columns: ColumnDef<NodeListPublic>[] = [
  {
    accessorKey: "title",
    header: "Title",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.title}</span>
    ),
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => {
      const description = row.original.description
      return (
        <span
          className={cn(
            "max-w-xs truncate block text-muted-foreground",
            !description && "italic",
          )}
        >
          {description || "No description"}
        </span>
      )
    },
  },
  {
    accessorKey: "created_at",
    header: "CREATED AT",
    cell: ({ row }) => {
      const createdAt = row.original.created_at
      if (!createdAt) return <span className="text-muted-foreground">N/A</span>
      return (
        <span className="text-muted-foreground">
          {new Intl.DateTimeFormat("en-US", {
            dateStyle: "medium",
            timeStyle: "short",
          }).format(new Date(createdAt))}
        </span>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <ListActionsMenu list={row.original} />
      </div>
    ),
  },
]
