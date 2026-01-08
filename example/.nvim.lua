local group = vim.api.nvim_create_augroup("resume_manager", { clear = true })

vim.api.nvim_create_autocmd("BufWritePost", {
	group = group,
	pattern = "*/dist/**/*.json",
	callback = function(event)
		local file_path = event.file
		local pdf_path = file_path:gsub("%.json$", ".pdf")

		local cmd = string.format("resume export %s --resume %s --theme jsonresume-theme-awesomish", pdf_path, file_path)

		vim.fn.jobstart(cmd, {
			on_exit = function(_, exit_code)
				if exit_code == 0 then
					vim.notify("Resume PDF generated: " .. pdf_path, vim.log.levels.INFO)
				else
					vim.notify("Resume generation failed for: " .. file_path, vim.log.levels.ERROR)
				end
			end,
		})
	end,
})

vim.api.nvim_create_autocmd("BufWritePost", {
	group = group,
	pattern = "*/profiles/**/*.json",
	callback = function(event)
		local file_path = event.file
		local cwd = vim.fn.getcwd()

		vim.fn.jobstart("resume_manager.py", {
			cwd = cwd,
			on_exit = function(_, exit_code)
				if exit_code == 0 then
					vim.notify("Resume manager completed successfully", vim.log.levels.INFO)
				else
					vim.notify("Resume manager failed with exit code: " .. exit_code, vim.log.levels.ERROR)
				end
			end,
		})
	end,
})
