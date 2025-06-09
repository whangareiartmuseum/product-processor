'use client'

import { useState, useEffect } from 'react'

interface InstagramPostDisplayProps {
  postData: {
    product_id: string
    product_title: string
    image_data: string
    caption: string
    full_caption?: string
    shop_url?: string
    next_post_time: string
    complementary_color: string
    posted?: boolean
    post_url?: string
  }
  onRegenerate: () => void
  onMarkPosted: (productId: string) => void
}

export function InstagramPostDisplay({ postData, onRegenerate, onMarkPosted }: InstagramPostDisplayProps) {
  const [timeUntilPost, setTimeUntilPost] = useState('')
  const [isPosting, setIsPosting] = useState(false)
  const [postResult, setPostResult] = useState<{ posted: boolean; url?: string } | null>(null)

  useEffect(() => {
    const updateTimer = () => {
      const now = new Date()
      const postTime = new Date(postData.next_post_time)
      const diff = postTime.getTime() - now.getTime()

      if (diff <= 0) {
        setTimeUntilPost('Ready to post!')
      } else {
        const hours = Math.floor(diff / (1000 * 60 * 60))
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
        const seconds = Math.floor((diff % (1000 * 60)) / 1000)
        setTimeUntilPost(`${hours}h ${minutes}m ${seconds}s`)
      }
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)

    return () => clearInterval(interval)
  }, [postData.next_post_time])

  // Check if already posted
  useEffect(() => {
    if (postData.posted && postData.post_url) {
      setPostResult({ posted: true, url: postData.post_url })
    }
  }, [postData.posted, postData.post_url])

  const handlePost = () => {
    // Mark as posted
    onMarkPosted(postData.product_id)
    // Generate a new post
    onRegenerate()
  }

  const handleActualPost = async () => {
    setIsPosting(true)
    try {
      const isVercel = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
      const endpoint = isVercel ? '/api/instagram-generate' : '/api/instagram/generate'
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ post: true })
      })

      const data = await response.json()
      
      if (data.posted) {
        setPostResult({ posted: true, url: data.post_url })
        // Automatically generate a new post after successful posting
        setTimeout(() => {
          onRegenerate()
        }, 2000)
      } else {
        setPostResult({ posted: false })
      }
    } catch (error) {
      console.error('Failed to post to Instagram:', error)
      setPostResult({ posted: false })
    } finally {
      setIsPosting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Timer and Controls */}
      <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-2xl font-bold mb-2">Next Post In:</h3>
            <p className="text-3xl font-mono">{timeUntilPost}</p>
            <p className="text-sm opacity-90 mt-2">
              Scheduled for: {new Date(postData.next_post_time).toLocaleString()}
            </p>
          </div>
          <div className="space-y-3">
            <button
              onClick={onRegenerate}
              className="block w-full px-6 py-3 bg-white text-purple-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Generate New Post
            </button>
            <button
              onClick={handleActualPost}
              disabled={isPosting}
              className={`block w-full px-6 py-3 rounded-lg font-semibold transition-colors ${
                isPosting 
                  ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                  : 'bg-pink-600 text-white hover:bg-pink-700'
              }`}
            >
              {isPosting ? 'Posting...' : 'Post to Instagram'}
            </button>
            <button
              onClick={handlePost}
              className="block w-full px-6 py-3 bg-gray-600 text-white rounded-lg font-semibold hover:bg-gray-700 transition-colors text-sm"
            >
              Mark as Posted (Manual)
            </button>
          </div>
        </div>
      </div>

      {/* Post Result Notification */}
      {postResult && (
        <div className={`rounded-lg p-4 ${
          postResult.posted 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          {postResult.posted ? (
            <div>
              <p className="text-green-800 font-semibold">✅ Successfully posted to Instagram!</p>
              {postResult.url && (
                <a 
                  href={postResult.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-green-600 underline text-sm mt-1 inline-block"
                >
                  View post on Instagram →
                </a>
              )}
            </div>
          ) : (
            <p className="text-red-800 font-semibold">❌ Failed to post to Instagram. Check your credentials.</p>
          )}
        </div>
      )}

      {/* Instagram Post Preview */}
      <div className="bg-gray-100 rounded-lg p-6">
        <h3 className="text-xl font-semibold mb-4 text-gray-800">Instagram Post Preview</h3>
        
        <div className="max-w-2xl mx-auto">
          {/* Instagram-style container */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full"></div>
              <div>
                <p className="font-semibold text-gray-900">whangarei_art_museum</p>
                <p className="text-xs text-gray-500">Whangārei Art Museum</p>
              </div>
            </div>

            {/* Image */}
            <div className="relative">
              <img 
                src={postData.image_data} 
                alt={postData.product_title}
                className="w-full"
              />
              <div className="absolute top-4 right-4 bg-white px-3 py-1 rounded-full shadow-md">
                <p className="text-sm font-medium text-gray-800">{postData.product_title}</p>
              </div>
            </div>

            {/* Caption */}
            <div className="p-4">
              <div className="mb-3 flex items-center space-x-6">
                <button className="hover:opacity-70 transition-opacity">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </button>
                <button className="hover:opacity-70 transition-opacity">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </button>
                <button className="hover:opacity-70 transition-opacity">
                  <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m9.632 4.316C18.114 15.062 18 14.518 18 14c0-.482.114-.938.316-1.342m0 2.684a3 3 0 110-2.684M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
              </div>

              <div className="space-y-2">
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{postData.full_caption || postData.caption}</p>
              </div>

              <p className="text-xs text-gray-500 mt-3">
                {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric' }).toUpperCase()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Product Details */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">Product Details</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-blue-700 font-medium">Product:</span>
            <span className="ml-2 text-blue-800">{postData.product_title}</span>
          </div>
          <div>
            <span className="text-blue-700 font-medium">Product ID:</span>
            <span className="ml-2 text-blue-800">{postData.product_id}</span>
          </div>
          <div>
            <span className="text-blue-700 font-medium">Background Color:</span>
            <span className="ml-2 text-blue-800">{postData.complementary_color}</span>
            <span 
              className="inline-block w-6 h-6 rounded ml-2 border border-gray-300"
              style={{ backgroundColor: postData.complementary_color }}
            ></span>
          </div>
          <div>
            <span className="text-blue-700 font-medium">Caption Length:</span>
            <span className="ml-2 text-blue-800">{postData.caption.split(' ').length} words</span>
          </div>
          {postData.shop_url && (
            <div className="col-span-2">
              <span className="text-blue-700 font-medium">Shop URL:</span>
              <a 
                href={postData.shop_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="ml-2 text-blue-600 underline"
              >
                {postData.shop_url}
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 