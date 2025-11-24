import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchWhitelist, createWhitelistEntry, updateWhitelistEntry, deleteWhitelistEntry } from '../api/whitelist'
import type { CreateWhitelistPayload, UpdateWhitelistPayload } from '../api/whitelist'

export function useWhitelist() {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['whitelist'],
    queryFn: fetchWhitelist,
  })

  const createMutation = useMutation({
    mutationFn: (payload: CreateWhitelistPayload) => createWhitelistEntry(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['whitelist'] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateWhitelistPayload }) =>
      updateWhitelistEntry(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['whitelist'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteWhitelistEntry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['whitelist'] })
    },
  })

  return {
    entries: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    addEntry: createMutation.mutateAsync,
    isAdding: createMutation.isPending,
    updateEntry: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    deleteEntry: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
  }
}
