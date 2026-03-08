import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { ListPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteList from "./DeleteList"
import EditList from "./EditList"

interface ListActionsMenuProps {
  list: ListPublic
}

export const ListActionsMenu = ({ list }: ListActionsMenuProps) => {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditList list={list} onSuccess={() => setOpen(false)} />
        <DeleteList id={list.id} onSuccess={() => setOpen(false)} />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
