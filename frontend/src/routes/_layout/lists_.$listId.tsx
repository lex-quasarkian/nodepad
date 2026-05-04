import {
	closestCenter,
	DndContext,
	type DragEndEvent,
	KeyboardSensor,
	PointerSensor,
	useSensor,
	useSensors,
} from "@dnd-kit/core";
import {
	SortableContext,
	sortableKeyboardCoordinates,
	useSortable,
	verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
	useMutation,
	useQueryClient,
	useSuspenseQuery,
} from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ChevronDown, ChevronRight, Plus } from "lucide-react";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ListsService, NodesService } from "@/client";
import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

function getListQueryOptions(listId: string) {
	return {
		queryFn: () => ListsService.readList({ id: listId }),
		queryKey: ["lists", listId],
	};
}

export const Route = createFileRoute("/_layout/lists_/$listId")({
	component: ListDetail,
});

interface Node {
	id: string;
	content: string;
	parent_id?: string | null;
	level: number;
	path: string;
	position: string;
}

function SortableNode({
	node,
	children,
}: {
	node: Node;
	children: (props: {
		attributes: any;
		listeners: any;
	}) => React.ReactNode;
}) {
	const {
		attributes,
		listeners,
		setNodeRef,
		transform,
		transition,
		isDragging,
	} = useSortable({ id: node.id });

	const style = {
		transform: CSS.Transform.toString(transform),
		transition,
		opacity: isDragging ? 0.5 : 1,
		zIndex: isDragging ? 50 : 1,
		position: "relative" as const,
	};

	return (
		<div ref={setNodeRef} style={style}>
			{children({ attributes, listeners })}
		</div>
	);
}

function ListDetail() {
	const { listId } = Route.useParams();
	return (
		<Suspense
			fallback={
				<div className="p-4 md:p-8 max-w-4xl mx-auto">
					<Skeleton className="h-10 w-64 mb-4" />
					<Skeleton className="h-4 w-full mb-8" />
					<div className="space-y-2">
						{[1, 2, 3, 4, 5].map((i) => (
							<Skeleton key={i} className="h-8 w-full" />
						))}
					</div>
				</div>
			}
		>
			<ListDetailContent listId={listId} />
		</Suspense>
	);
}

function ListDetailContent({ listId }: { listId: string }) {
	const { resolvedTheme } = useTheme();
	const queryClient = useQueryClient();
	const { data: list } = useSuspenseQuery(getListQueryOptions(listId));
	const navigate = useNavigate();

	const [collapsedIds, setCollapsedIds] = useState<Set<string>>(new Set());
	const [editingId, setEditingId] = useState<string | null>(null);
	const [editingContent, setEditingContent] = useState("");
	const [addingToId, setAddingToId] = useState<string | null>(null);
	const [newContent, setNewContent] = useState("");

	const editInputRef = useRef<HTMLInputElement>(null);
	const newInputRef = useRef<HTMLInputElement>(null);

	const updateMutation = useMutation({
		mutationFn: (data: {
			id: string;
			content?: string;
			parent_id?: string;
			level?: number;
		}) => NodesService.patchNode({ id: data.id, requestBody: data }),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["lists", listId] });
		},
	});

	const createMutation = useMutation({
		mutationFn: (data: {
			content: string;
			parent_id?: string;
			id?: string;
			position?: string;
		}) =>
			NodesService.createNode({
				nodelistId: listId,
				requestBody: data,
			}),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["lists", listId] });
			setAddingToId(null);
			setNewContent("");
		},
	});

	const reorderMutation = useMutation({
		mutationFn: (data: { id: string; before_id?: string; after_id?: string }) =>
			NodesService.reorderNode({
				id: data.id,
				beforeId: data.before_id,
				afterId: data.after_id,
			}),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["lists", listId] });
		},
	});

	const deleteMutation = useMutation({
		mutationFn: (id: string) => NodesService.deleteNode({ id }),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["lists", listId] });
		},
	});

	const sensors = useSensors(
		useSensor(PointerSensor, {
			activationConstraint: {
				distance: 8,
			},
		}),
		useSensor(KeyboardSensor, {
			coordinateGetter: sortableKeyboardCoordinates,
		}),
	);

	const sortedNodes = useMemo<Node[]>(() => {
		if (!list.nodes) return [];
		const nodes = list.nodes.filter((n): n is NonNullable<typeof n> => !!n);
		const map = new Map<string | null, Node[]>();
		for (const n of nodes as Node[]) {
			const pid = n.parent_id || null;
			if (!map.has(pid)) map.set(pid, []);
			map.get(pid)!.push(n);
		}

		for (const group of map.values()) {
			group.sort((a, b) => Number(a.position) - Number(b.position));
		}

		const result: Node[] = [];
		const traverse = (pid: string | null) => {
			const children = map.get(pid) || [];
			for (const child of children) {
				result.push(child);
				traverse(child.id);
			}
		};
		traverse(null);
		return result;
	}, [list.nodes]);

	const visibleNodes = useMemo<Node[]>(() => {
		const result: Node[] = [];
		let skipPrefix: string | null = null;
		for (const node of sortedNodes) {
			if (skipPrefix && node.path.startsWith(skipPrefix)) continue;
			result.push(node);
			if (collapsedIds.has(node.id)) skipPrefix = node.path + ".";
			else skipPrefix = null;
		}
		return result;
	}, [sortedNodes, collapsedIds]);

	const [lastDeletedNode, setLastDeletedNode] = useState<Node | null>(null);

	const handleDeleteNode = useCallback(
		(id: string) => {
			const node = sortedNodes.find((n) => n.id === id);
			if (node) {
				setLastDeletedNode(node);
				deleteMutation.mutate(id);
				setEditingId(null);
			}
		},
		[sortedNodes, deleteMutation],
	);

	const handleUndoDelete = useCallback(() => {
		if (lastDeletedNode) {
			createMutation.mutate({
				content: lastDeletedNode.content,
				parent_id: lastDeletedNode.parent_id || undefined,
				// We pass the old position to restore it exactly
				position: lastDeletedNode.position,
				// We also try to restore the ID if the backend supports it
				id: lastDeletedNode.id,
			});
			setLastDeletedNode(null);
		}
	}, [lastDeletedNode, createMutation]);

	useEffect(() => {
		const handleGlobalKeyDown = (e: KeyboardEvent) => {
			if ((e.ctrlKey || e.metaKey) && e.key === "z") {
				if (!editingId && !addingToId) {
					e.preventDefault();
					handleUndoDelete();
				}
			}
		};
		window.addEventListener("keydown", handleGlobalKeyDown);
		return () => window.removeEventListener("keydown", handleGlobalKeyDown);
	}, [handleUndoDelete, editingId, addingToId]);

	const handleStartEdit = useCallback((node: Node) => {
		setEditingId(node.id);
		setEditingContent(node.content);
	}, []);

	const handleSaveEdit = useCallback(() => {
		if (editingId) {
			const node = sortedNodes.find((n) => n.id === editingId);
			if (node && editingContent !== node.content) {
				updateMutation.mutate({ id: editingId, content: editingContent });
			}
			setEditingId(null);
		}
	}, [editingId, editingContent, sortedNodes, updateMutation]);

	const handleIndent = useCallback(
		(nodeId: string) => {
			const idx = sortedNodes.findIndex((n) => n.id === nodeId);
			if (idx === -1) return;
			const node = sortedNodes[idx];
			const prevNode = idx > 0 ? sortedNodes[idx - 1] : null;
			const maxAllowed = prevNode ? prevNode.level + 1 : 0;

			const newLevel = Math.min((node.level || 0) + 1, maxAllowed);
			if (newLevel !== node.level) {
				updateMutation.mutate({ id: nodeId, level: newLevel });
			}
		},
		[sortedNodes, updateMutation],
	);

	const handleOutdent = useCallback(
		(nodeId: string) => {
			const node = sortedNodes.find((n) => n.id === nodeId);
			if (!node) return;
			const newLevel = Math.max((node.level || 0) - 1, 0);
			if (newLevel !== node.level) {
				updateMutation.mutate({ id: nodeId, level: newLevel });
			}
		},
		[sortedNodes, updateMutation],
	);

	const handleEditKeyDown = useCallback(
		(e: React.KeyboardEvent) => {
			const actions: Record<string, () => void> = {
				Tab: () => {
					e.preventDefault();
					e.stopPropagation();
					if (e.shiftKey) handleOutdent(editingId!);
					else handleIndent(editingId!);
				},
				ArrowUp: () => {
					e.preventDefault();
					const idx = visibleNodes.findIndex((n) => n.id === editingId);
					if (idx > 0) {
						handleSaveEdit();
						handleStartEdit(visibleNodes[idx - 1]);
					}
				},
				ArrowDown: () => {
					e.preventDefault();
					const idx = visibleNodes.findIndex((n) => n.id === editingId);
					if (idx < visibleNodes.length - 1) {
						handleSaveEdit();
						handleStartEdit(visibleNodes[idx + 1]);
					}
				},
				Enter: () => {
					if (e.shiftKey) {
						handleSaveEdit();
						setAddingToId(editingId);
					} else {
						editInputRef.current?.blur();
					}
				},
				Backspace: () => {
					if (editingContent === "") {
						e.preventDefault();
						handleDeleteNode(editingId!);
					}
				},
				Escape: () => {
					setEditingId(null);
				},
			};

			if (actions[e.key]) {
				actions[e.key]();
			}
		},
		[
			editingId,
			handleIndent,
			handleOutdent,
			visibleNodes,
			handleSaveEdit,
			handleStartEdit,
			editingContent,
			handleDeleteNode,
		],
	);

	const handleDragEnd = (event: DragEndEvent) => {
		const { active, over } = event;
		if (!over || active.id === over.id) return;

		const oldIndex = sortedNodes.findIndex((n) => n.id === active.id);
		const newIndex = sortedNodes.findIndex((n) => n.id === over.id);

		if (oldIndex !== -1 && newIndex !== -1) {
			const draggedNode = sortedNodes[oldIndex];
			const targetNode = sortedNodes[newIndex];

			if (
				!draggedNode ||
				!targetNode ||
				draggedNode.parent_id !== targetNode.parent_id
			) {
				return;
			}

			let before_id: string | undefined;
			let after_id: string | undefined;

			if (newIndex > oldIndex) {
				after_id = targetNode.id;
				const nextNode = sortedNodes[newIndex + 1];
				if (nextNode && nextNode.parent_id === draggedNode.parent_id) {
					before_id = nextNode.id;
				}
			} else {
				before_id = targetNode.id;
				const prevNode = sortedNodes[newIndex - 1];
				if (prevNode && prevNode.parent_id === draggedNode.parent_id) {
					after_id = prevNode.id;
				}
			}

			reorderMutation.mutate({ id: draggedNode.id, before_id, after_id });
		}
	};

	useEffect(() => {
		if (editingId && editInputRef.current) {
			editInputRef.current.focus();
		}
	}, [editingId, list]);

	useEffect(() => {
		if (addingToId && newInputRef.current) {
			newInputRef.current.focus();
		}
	}, [addingToId]);


	const toggleCollapse = (id: string) => {
		setCollapsedIds((prev) => {
			const next = new Set(prev);
			if (next.has(id)) next.delete(id);
			else next.add(id);
			return next;
		});
	};

	const handleSaveNew = () => {
		if (newContent.trim()) {
			createMutation.mutate({
				content: newContent,
				parent_id: addingToId === "root" ? undefined : (addingToId as string),
			});
		}
		setAddingToId(null);
		setNewContent("");
	};

	const handleNewKeyDown = (e: React.KeyboardEvent) => {
		if (e.key === "Enter") {
			newInputRef.current?.blur();
		} else if (e.key === "Escape") {
			setAddingToId(null);
		}
	};

	const nodesByParent = useMemo(() => {
		const map = new Map<string | null, Node[]>();
		for (const n of sortedNodes) {
			const pid = n.parent_id || null;
			if (!map.has(pid)) map.set(pid, []);
			map.get(pid)!.push(n);
		}
		return map;
	}, [sortedNodes]);

	const renderNode = (node: Node) => {
		const children = nodesByParent.get(node.id) || [];
		const isCollapsed = collapsedIds.has(node.id);

		return (
			<SortableNode key={node.id} node={node}>
				{({ attributes, listeners }: any) => (
					<div className="flex flex-col">
						<div
							style={{ paddingLeft: `${(node.level || 0) * 20}px` }}
							className="flex items-center gap-1 group min-h-[22px]"
						>
							<div className="flex items-center gap-0.5 w-10 justify-end shrink-0">
								<button
									onClick={() => setAddingToId(node.id)}
									className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-accent rounded transition-all"
									type="button"
									title="Add child node"
								>
									<Plus className="h-3 w-3 text-muted-foreground" />
								</button>
								<div className="w-4 flex items-center justify-center">
									{children.length > 0 && (
										<button
											onClick={() => toggleCollapse(node.id)}
											className="hover:bg-accent rounded p-0.5 transition-colors"
											type="button"
										>
											{isCollapsed ? (
												<ChevronRight className="h-3 w-3" />
											) : (
												<ChevronDown className="h-3 w-3" />
											)}
										</button>
									)}
								</div>
							</div>
							<div
								{...attributes}
								{...listeners}
								className={cn(
									"h-1.5 w-1.5 rounded-full bg-foreground shrink-0 transition-all duration-200 cursor-grab active:cursor-grabbing",
									editingId === node.id && "z-10",
								)}
								style={
									editingId === node.id
										? {
												boxShadow: `0 0 0 1px ${resolvedTheme === "dark" ? "#427AB5" : "#F7DD7D"}, 
                                    0 0 0 2px ${resolvedTheme === "dark" ? "#427AB599" : "#F7DD7D99"}, 
                                    0 0 0 3px ${resolvedTheme === "dark" ? "#427AB533" : "#F7DD7D33"}`,
											}
										: {}
								}
							/>
							<div className="flex items-center gap-2 w-full pr-4">
								{editingId === node.id ? (
									<Input
										ref={editInputRef}
										value={editingContent}
										onChange={(e) => setEditingContent(e.target.value)}
										onBlur={handleSaveEdit}
										onKeyDown={handleEditKeyDown}
										className="h-7 py-1 text-sm border-none bg-transparent shadow-none focus-visible:ring-0 focus-visible:ring-offset-0 px-1 -ml-1"
									/>
								) : (
									<button
										type="button"
										className="text-sm text-left leading-tight whitespace-pre-wrap cursor-pointer hover:underline underline-offset-4 px-1 -ml-1 transition-all w-full min-h-[1.25rem] flex items-center"
										onClick={() => handleStartEdit(node)}
									>
										{node.content}
									</button>
								)}
							</div>
						</div>
						{addingToId === node.id && (
							<div
								style={{
									paddingLeft: `${((node.level || 0) + 1) * 20}px`,
								}}
								className="flex items-center gap-1 min-h-[22px]"
							>
								<div className="w-10 shrink-0" />
								<div className="h-1.5 w-1.5 rounded-full bg-foreground shrink-0 opacity-50" />
								<Input
									ref={newInputRef}
									value={newContent}
									onChange={(e) => setNewContent(e.target.value)}
									onBlur={handleSaveNew}
									onKeyDown={handleNewKeyDown}
									placeholder="New item..."
									className="h-7 py-1 text-sm mr-4"
								/>
							</div>
						)}
						{!isCollapsed && children.map((child) => renderNode(child))}
					</div>
				)}
			</SortableNode>
		);
	};

	const dateStr = list.updated_at || list.created_at;
	let formattedDate = "";
	if (dateStr) {
		const d = new Date(dateStr);
		formattedDate = d.toLocaleString();
	}

	return (
		<div className="p-4 md:p-8 max-w-4xl mx-auto">
			{typeof document !== "undefined" &&
				createPortal(
					<div className="flex items-center gap-4 flex-1 min-w-0">
						<Button
							variant="ghost"
							size="sm"
							onClick={() => navigate({ to: "/" })}
							className="shrink-0 gap-2"
						>
							Back
						</Button>
						<div className="flex flex-col min-w-0">
							<h1 className="text-sm font-semibold truncate">{list.title}</h1>
							<div className="flex items-center gap-2">
								{list.description && (
									<p className="text-xs text-muted-foreground truncate">
										{list.description}
									</p>
								)}
								{formattedDate && (
									<span className="text-[10px] text-muted-foreground/50 whitespace-nowrap">
										• Updated {formattedDate}
									</span>
								)}
							</div>
						</div>
					</div>,
					document.getElementById("header-portal")!,
				)}

			<div className="flex flex-col gap-6">
				<div className="flex flex-col gap-0.5">
					<DndContext
						sensors={sensors}
						collisionDetection={closestCenter}
						onDragEnd={handleDragEnd}
					>
						<SortableContext
							items={visibleNodes.map((n) => n.id)}
							strategy={verticalListSortingStrategy}
						>
							{nodesByParent.get(null)?.map((node) => renderNode(node))}
						</SortableContext>
					</DndContext>
				</div>

				{addingToId === "root" ? (
					<div className="flex items-center gap-1 min-h-[22px] mt-1">
						<div className="w-10 shrink-0" />
						<div className="h-1.5 w-1.5 rounded-full bg-foreground shrink-0 opacity-50" />
						<Input
							ref={newInputRef}
							value={newContent}
							onChange={(e) => setNewContent(e.target.value)}
							onBlur={handleSaveNew}
							onKeyDown={handleNewKeyDown}
							placeholder="New root item..."
							className="h-7 py-1 text-sm mr-4"
						/>
					</div>
				) : (
					<div className="flex items-center gap-1 min-h-[22px] mt-2">
						<div className="w-10 flex items-center justify-end shrink-0 pr-1">
							<button
								onClick={() => setAddingToId("root")}
								className="p-0.5 hover:bg-accent rounded transition-all"
								title="Add root node"
								type="button"
							>
								<Plus className="h-4 w-4 text-muted-foreground" />
							</button>
						</div>
					</div>
				)}
			</div>
		</div>
	);
}
