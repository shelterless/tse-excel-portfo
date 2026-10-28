using System.Xml.Linq;
using Xunit;

namespace TseExcel.AddIn.Tests;

public class ArchitectureContractTests
{
    [Fact]
    public void Solution_HasExactlyFourShortNamedProductionProjectsAndUsefulTestProjects()
    {
        string root = FindRepositoryRoot();
        XDocument solution = XDocument.Load(Path.Combine(root, "TseExcel.slnx"));
        string[] projects = solution.Descendants("Project").Select(project => (string)project.Attribute("Path")!).ToArray();
        Assert.Equal(new[] { "src/AddIn/AddIn.csproj", "src/Application/Application.csproj",
            "src/Domain/Domain.csproj", "src/Infrastructure/Infrastructure.csproj" },
            projects.Where(path => path.StartsWith("src/", StringComparison.Ordinal)).Order());
        Assert.Equal(new[] { "tests/AddIn.Tests/AddIn.Tests.csproj", "tests/Application.Tests/Application.Tests.csproj",
            "tests/Infrastructure.Tests/Infrastructure.Tests.csproj" },
            projects.Where(path => path.StartsWith("tests/", StringComparison.Ordinal)).Order());
        Assert.All(projects, path => Assert.True(File.Exists(Path.Combine(root, path)), path));
        Assert.Equal(4, Directory.GetFiles(Path.Combine(root, "src"), "*.csproj", SearchOption.AllDirectories).Length);
    }

    [Theory]
    [InlineData("Domain", "")]
    [InlineData("Application", "../Domain/Domain.csproj")]
    [InlineData("Infrastructure", "../Application/Application.csproj")]
    [InlineData("AddIn", "../Application/Application.csproj;../Infrastructure/Infrastructure.csproj")]
    public void Projects_EnforceApprovedIdentitiesDependenciesAndHostBoundary(string name, string expectedReferences)
    {
        XDocument project = XDocument.Load(Path.Combine(FindRepositoryRoot(), "src", name, name + ".csproj"));
        Assert.Equal("TseExcel." + name, project.Descendants("AssemblyName").Single().Value);
        Assert.Equal("TseExcel." + name, project.Descendants("RootNamespace").Single().Value);
        Assert.Equal(name == "AddIn" ? "net10.0-windows" : "net10.0", project.Descendants("TargetFramework").Single().Value);
        Assert.Equal(expectedReferences.Split(';', StringSplitOptions.RemoveEmptyEntries),
            project.Descendants("ProjectReference").Select(reference => (string)reference.Attribute("Include")!));
        if (name == "AddIn")
        {
            XElement package = Assert.Single(project.Descendants("PackageReference"));
            Assert.Equal("ExcelDna.AddIn", (string?)package.Attribute("Include"));
            Assert.Equal("1.9.0", (string?)package.Attribute("Version"));
            Assert.Equal("true", project.Descendants("UseWindowsForms").Single().Value);
            Assert.Equal("true", project.Descendants("ExcelAddInExplicitExports").Single().Value);
        }
        else
        {
            Assert.Empty(project.Descendants("PackageReference"));
            Assert.Empty(project.Descendants("UseWindowsForms"));
            Assert.Empty(project.Descendants("FrameworkReference"));
        }
    }

    [Fact]
    public void AddIn_ReferencesInfrastructureOnlyInComposition()
    {
        string directory = Path.Combine(FindRepositoryRoot(), "src", "AddIn");
        foreach (string file in Directory.GetFiles(directory, "*.cs", SearchOption.AllDirectories))
        {
            string relative = Path.GetRelativePath(directory, file);
            if (relative.StartsWith("obj" + Path.DirectorySeparatorChar, StringComparison.Ordinal) ||
                relative.StartsWith("bin" + Path.DirectorySeparatorChar, StringComparison.Ordinal) ||
                relative.StartsWith("Composition" + Path.DirectorySeparatorChar, StringComparison.Ordinal)) continue;
            string source = File.ReadAllText(file);
            Assert.DoesNotContain("TseExcel.Infrastructure", source);
            Assert.DoesNotContain("File.", source);
            Assert.DoesNotContain("Directory.", source);
        }
    }

    internal static string FindRepositoryRoot()
    {
        for (DirectoryInfo? directory = new(AppContext.BaseDirectory); directory is not null; directory = directory.Parent)
        {
            if (File.Exists(Path.Combine(directory.FullName, "TseExcel.slnx"))) return directory.FullName;
        }
        throw new DirectoryNotFoundException("Run repository architecture tests from the repository build output.");
    }
}
