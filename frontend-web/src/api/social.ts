import axiosClient from './axiosClient'
import type { FriendResponse, FriendRequestResponse, ActivityFeedItem, UserSearchResult } from '../types'

export const getFriends = () => axiosClient.get<FriendResponse[]>('/social/friends')
export const getFriendRequests = () => axiosClient.get<FriendRequestResponse[]>('/social/friends/requests')
export const sendFriendRequest = (addressee_id: string) =>
  axiosClient.post('/social/friends/request', { addressee_id })
export const acceptFriendRequest = (friendship_id: string) =>
  axiosClient.post('/social/friends/accept', { friendship_id })
export const getFeed = () => axiosClient.get<ActivityFeedItem[]>('/social/feed')
export const searchUsers = (q: string) =>
  axiosClient.get<UserSearchResult[]>('/social/users/search', { params: { q } })
