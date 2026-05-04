import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { Suspense } from "react"

import { ListsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import AddList from "@/components/Lists/AddList"
import { columns } from "@/components/Lists/columns"
import PendingLists from "@/components/Pending/PendingLists"

function getListsQueryOptions() {
  return {
    queryFn: () => ListsService.readLists({ skip: 0, limit: 100 }),
    queryKey: ["lists"],
  }
}

export const Route = createFileRoute("/_layout/lists")({
  component: Lists,
  head: () => ({
    meta: [
      {
        title: "Lists - FastAPI Template",
      },
    ],
  }),
})

function ListsTableContent() {
  const { data: lists } = useSuspenseQuery(getListsQueryOptions())

  if (lists.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">You don't have any lists yet</h3>
        <p className="text-muted-foreground">Add a new list to get started</p>
      </div>
    )
  }

  return <DataTable columns={columns} data={lists.data} />
}

function ListsTable() {
  return (
    <Suspense fallback={<PendingLists />}>
      <ListsTableContent />
    </Suspense>
  )
}

function Lists() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Lists</h1>
          <p className="text-muted-foreground">Create and manage your lists</p>
        </div>
        <AddList />
      </div>
      <ListsTable />
    </div>
  )
}
