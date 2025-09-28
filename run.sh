#curl 'https://api.notion.com/v1/blocks/1b7e1e3e265c80ceb883c0c58b8fb180/children?page_size=100' \
#  -H 'Authorization: Bearer '"$NOTION_TOKEN"'' \
#  -H "Notion-Version: 2022-06-28"

curl -X PATCH 'https://api.notion.com/v1/blocks/1b7e1e3e265c80ceb883c0c58b8fb180/children' \
  -H 'Authorization: Bearer '"$NOTION_TOKEN"'' \
  -H "Content-Type: application/json" \
  -H "Notion-Version: 2022-06-28" \
  --data '{
"after": "1b7e1e3e265c80ceb883c0c58b8fb180",
	"children": [
		{
			"object": "block",
			"type": "heading_2",
			"heading_2": {
				"rich_text": [{ "type": "text", "text": { "content": "Lacinato kale" } }]
			}
		}
	]
}'

#    {
#      "object": "block",
#      "id": "1b7e1e3e-265c-819a-864f-d3fbd3fff5d3",
#      "parent": {
#        "type": "page_id",
#        "page_id": "1b7e1e3e-265c-80ce-b883-c0c58b8fb180"
#      },
#      "created_time": "2025-03-15T01:38:00.000Z",
#      "last_edited_time": "2025-03-15T01:38:00.000Z",
#      "created_by": {
#        "object": "user",
#        "id": "a901243a-299b-467a-a830-f248e86dbea8"
#      },
#      "last_edited_by": {
#        "object": "user",
#        "id": "a901243a-299b-467a-a830-f248e86dbea8"
#      },
#      "has_children": true,
#      "archived": false,
#      "in_trash": false,
#      "type": "child_page",
#      "child_page": {
#        "title": "perf"
#      }
#    },
# {
#      "object": "block",
#      "id": "1b7e1e3e-265c-8127-92c7-dd59f0042c5e",
#      "parent": {
#        "type": "page_id",
#        "page_id": "1b7e1e3e-265c-80ce-b883-c0c58b8fb180"
#      },
#      "created_time": "2025-03-15T01:03:00.000Z",
#      "last_edited_time": "2025-03-15T03:15:00.000Z",
#      "created_by": {
#        "object": "user",
#        "id": "a901243a-299b-467a-a830-f248e86dbea8"
#      },
#      "last_edited_by": {
#        "object": "user",
#        "id": "5d28dab1-a9c9-4db1-b473-5975aa70be47"
#      },
#      "has_children": true,
#      "archived": false,
#      "in_trash": false,
#      "type": "child_page",
#      "child_page": {
#        "title": "how-to"
#      }
#    },
#
