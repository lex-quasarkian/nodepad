import { expect, test } from "@playwright/test"
import { createUser } from "./utils/privateApi"
import {
  randomEmail,
  randomListDescription,
  randomListTitle,
  randomPassword,
} from "./utils/random"
import { logInUser } from "./utils/user"

test("Lists page is accessible and shows correct title", async ({ page }) => {
  await page.goto("/lists")
  await expect(page.getByRole("heading", { name: "Lists" })).toBeVisible()
  await expect(page.getByText("Create and manage your lists")).toBeVisible()
})

test("Add List button is visible", async ({ page }) => {
  await page.goto("/lists")
  await expect(page.getByRole("button", { name: "Add List" })).toBeVisible()
})

test.describe("Lists management", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  const password = randomPassword()

  test.beforeAll(async () => {
    email = randomEmail()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
    await page.goto("/lists")
  })

  test("Create a new list successfully", async ({ page }) => {
    const title = randomListTitle()
    const description = randomListDescription()

    await page.getByRole("button", { name: "Add List" }).click()
    await page.getByLabel("Title").fill(title)
    await page.getByLabel("Description").fill(description)
    await page.getByRole("button", { name: "Save" }).click()

    await expect(page.getByText("List created successfully")).toBeVisible()
    await expect(page.getByText(title)).toBeVisible()
  })

  test("Create list with only required fields", async ({ page }) => {
    const title = randomListTitle()

    await page.getByRole("button", { name: "Add List" }).click()
    await page.getByLabel("Title").fill(title)
    await page.getByRole("button", { name: "Save" }).click()

    await expect(page.getByText("List created successfully")).toBeVisible()
    await expect(page.getByText(title)).toBeVisible()
  })

  test("Cancel list creation", async ({ page }) => {
    await page.getByRole("button", { name: "Add List" }).click()
    await page.getByLabel("Title").fill("Test List")
    await page.getByRole("button", { name: "Cancel" }).click()

    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("Title is required", async ({ page }) => {
    await page.getByRole("button", { name: "Add List" }).click()
    await page.getByLabel("Title").fill("")
    await page.getByLabel("Title").blur()

    await expect(page.getByText("Title is required")).toBeVisible()
  })

  test.describe("Edit and Delete", () => {
    let listTitle: string

    test.beforeEach(async ({ page }) => {
      listTitle = randomListTitle()

      await page.getByRole("button", { name: "Add List" }).click()
      await page.getByLabel("Title").fill(listTitle)
      await page.getByRole("button", { name: "Save" }).click()
      await expect(page.getByText("List created successfully")).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()
    })

    test("Edit a list successfully", async ({ page }) => {
      const listRow = page.getByRole("row").filter({ hasText: listTitle })
      await listRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Edit List" }).click()

      const updatedTitle = randomListTitle()
      await page.getByLabel("Title").fill(updatedTitle)
      await page.getByRole("button", { name: "Save" }).click()

      await expect(page.getByText("List updated successfully")).toBeVisible()
      await expect(page.getByText(updatedTitle)).toBeVisible()
    })

    test("Delete a list successfully", async ({ page }) => {
      const listRow = page.getByRole("row").filter({ hasText: listTitle })
      await listRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Delete List" }).click()

      await page.getByRole("button", { name: "Delete" }).click()

      await expect(
        page.getByText("The list was deleted successfully"),
      ).toBeVisible()
      await expect(page.getByText(listTitle)).not.toBeVisible()
    })
  })
})

test.describe("Lists empty state", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Shows empty state message when no lists exist", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/lists")

    await expect(page.getByText("You don't have any lists yet")).toBeVisible()
    await expect(page.getByText("Add a new list to get started")).toBeVisible()
  })
})
