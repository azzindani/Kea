
if __name__ == "__main__":
    import asyncio
    
    async def main():
        server = AcademicServer()
        await server.run()
        
    asyncio.run(main())
