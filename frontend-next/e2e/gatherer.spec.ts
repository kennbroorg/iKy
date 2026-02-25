import { test, expect } from "@playwright/test";

test("search bar accepts input and shows module grid", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/gatherer/);
  const searchInput = page.getByPlaceholder(/email or username/i);
  await expect(searchInput).toBeVisible();
  await searchInput.fill("test@example.com");
  await expect(page.getByText(/email/i)).toBeVisible();
});

test("sidebar navigation works", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /profile/i }).click();
  await expect(page).toHaveURL(/profile/);
  await page.getByRole("link", { name: /timeline/i }).click();
  await expect(page).toHaveURL(/timeline/);
  await page.getByRole("link", { name: /api keys/i }).click();
  await expect(page).toHaveURL(/apikeys/);
});
