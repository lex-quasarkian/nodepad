import { Briefcase, Home, Users } from "lucide-react"
import { useParams } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { ListsService } from "@/client"

import { SidebarAppearance } from "@/components/Common/Appearance"
import { Logo } from "@/components/Common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import useAuth from "@/hooks/useAuth"
import { type Item, Main } from "./Main"
import { User } from "./User"

export function AppSidebar() {
  const { user: currentUser } = useAuth()

  const params = useParams({ strict: false }) as Record<string, string>
  const listId = params?.listId

  const { data: list } = useQuery({
    queryKey: ["lists", listId],
    queryFn: () => ListsService.readList({ id: listId as string }),
    enabled: !!listId,
  })

  const baseItems: Item[] = []
  
  if (listId && list) {
    baseItems.push({ icon: Home, title: list.title, path: `/lists/${listId}` })
  }
  
  baseItems.push({ icon: Briefcase, title: "Lists", path: "/lists" })

  const items = currentUser?.is_superuser
    ? [...baseItems, { icon: Users, title: "Admin", path: "/admin" }]
    : baseItems

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
      </SidebarHeader>
      <SidebarContent>
        <Main items={items} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarAppearance />
        <User user={currentUser} />
      </SidebarFooter>
    </Sidebar>
  )
}

export default AppSidebar
