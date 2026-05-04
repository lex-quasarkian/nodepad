import { expect, test } from "@playwright/test"
import { logInUser } from "./utils/user"

test.describe("Nodes management", () => {
  test("Edit a node content via click and Enter", async ({ page }) => {
    // 1. Login as admin (has the default list from init_db)
    await logInUser(page, "admin@nodepad.io", "Gr33nWh33lBr!ck")
    
    // 2. Go to lists
    await page.goto("/lists")
    
    // 3. Find the Chamonix list and navigate to it
    await expect(page.getByText("Weekend Getaway: Chamonix")).toBeVisible()
    const listRow = page.getByRole("row").filter({ hasText: "Weekend Getaway: Chamonix" })
    const listId = await listRow.locator("td").first().innerText()
    await page.getByRole("link", { name: listId }).click()

    // 4. Wait for nodes to load
    await expect(page.getByText("Logistical Prep")).toBeVisible()

    // 5. Click on a node to edit (Confirm Airbnb...)
    const nodeText = "Confirm Airbnb check-in time"
    const nodeElement = page.getByRole("button", { name: nodeText })
    await nodeElement.click()

    // 6. Type new text and press Enter
    const newText = "Confirm Airbnb check-in time (Updated)"
    // The input should appear with the current text as value
    const input = page.locator('input')
    await expect(input).toHaveValue(nodeText)
    await input.fill(newText)
    await input.press("Enter")

    // 7. Verify the input is gone and the new text is visible
    await expect(input).not.toBeVisible()
    await expect(page.getByRole("button", { name: newText })).toBeVisible()
    
    // 8. Reload the page to verify persistence
    await page.reload()
    await expect(page.getByRole("button", { name: newText })).toBeVisible()
  })
})
