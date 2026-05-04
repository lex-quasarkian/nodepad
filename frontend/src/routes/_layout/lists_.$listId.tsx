import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Suspense } from "react"
import { ListsService } from "@/client"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"

function getListQueryOptions(listId: string) {
  return {
    queryFn: () => ListsService.readList({ id: listId }),
    queryKey: ["lists", listId],
  }
}

export const Route = createFileRoute("/_layout/lists_/$listId")({
  component: ListDetail,
})

function ListDetailContent({ listId }: { listId: string }) {
  const { data: list } = useSuspenseQuery(getListQueryOptions(listId))
  const navigate = useNavigate()

  const dateStr = list.updated_at || list.created_at
  let formattedDate = ""
  if (dateStr) {
    const d = new Date(dateStr)
    const dd = String(d.getDate()).padStart(2, "0")
    const mm = String(d.getMonth() + 1).padStart(2, "0")
    const yyyy = d.getFullYear()
    const hh = String(d.getHours()).padStart(2, "0")
    const min = String(d.getMinutes()).padStart(2, "0")
    formattedDate = `${dd}/${mm}/${yyyy}, ${hh}:${min}`
  }

  // Find the node with the minimum position
  const minNode = list.nodes?.reduce((min, current) => {
    if (!min) return current
    if (!current) return min
    const minPos = parseFloat(min.position)
    const currentPos = parseFloat(current.position)
    return currentPos < minPos ? current : min
  }, list.nodes[0] || null)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <div className="flex justify-between items-start">
          <h1 className="text-2xl font-bold tracking-tight pr-8">{list.title}</h1>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate({ to: "/lists" })}
            title="Close Workspace"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        <div className="flex justify-between items-center">
          <p className="text-sm text-muted-foreground">ID: {list.id}</p>
          <p className="text-sm text-muted-foreground">{formattedDate}</p>
        </div>
        {list.description && (
          <p className="text-xl font-semibold mt-2">{list.description}</p>
        )}
      </div>

      <div className="mt-6 border rounded-lg p-6 bg-card">
        {minNode ? (
          <div className="flex flex-col gap-2">
            <p className="text-sm text-muted-foreground">
              Position: {minNode.position}
            </p>
            <div className="p-4 bg-muted/50 rounded-md">
              <p className="whitespace-pre-wrap">{minNode.content}</p>
            </div>
          </div>
        ) : (
          <p className="text-muted-foreground italic">No nodes in this list.</p>
        )}
      </div>
    </div>
  )
}

function ListDetail() {
  const { listId } = Route.useParams()

  return (
    <Suspense
      fallback={
        <div className="flex flex-col gap-6">
          <Skeleton className="h-10 w-[200px]" />
          <Skeleton className="h-6 w-[300px]" />
          <Skeleton className="h-6 w-[250px]" />
          <Skeleton className="h-[200px] w-full mt-6" />
        </div>
      }
    >
      <ListDetailContent listId={listId} />
    </Suspense>
  )
}
