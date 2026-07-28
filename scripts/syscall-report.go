//go:build linux && amd64

package main

import (
	"flag"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"

	"github.com/langgenius/dify-sandbox/internal/static/python_syscall"
)

func uniqueSorted(values ...[]int) []int {
	seen := make(map[int]struct{})
	for _, list := range values {
		for _, value := range list {
			seen[value] = struct{}{}
		}
	}

	result := make([]int, 0, len(seen))
	for value := range seen {
		result = append(result, value)
	}
	sort.Ints(result)
	return result
}

func parseSyscalls(raw string) ([]int, error) {
	if strings.TrimSpace(raw) == "" {
		return []int{}, nil
	}

	values := make([]int, 0)
	for _, item := range strings.Split(raw, ",") {
		value, err := strconv.Atoi(strings.TrimSpace(item))
		if err != nil {
			return nil, fmt.Errorf("invalid syscall number %q: %w", item, err)
		}
		values = append(values, value)
	}
	return uniqueSorted(values), nil
}

func intersect(values []int, allowed []int) []int {
	allowedSet := make(map[int]struct{}, len(allowed))
	for _, value := range allowed {
		allowedSet[value] = struct{}{}
	}

	result := make([]int, 0)
	for _, value := range values {
		if _, ok := allowedSet[value]; ok {
			result = append(result, value)
		}
	}
	return result
}

func difference(values []int, allowed []int) []int {
	allowedSet := make(map[int]struct{}, len(allowed))
	for _, value := range allowed {
		allowedSet[value] = struct{}{}
	}

	result := make([]int, 0)
	for _, value := range values {
		if _, ok := allowedSet[value]; !ok {
			result = append(result, value)
		}
	}
	return result
}

func formatSyscalls(values []int) string {
	items := make([]string, 0, len(values))
	for _, value := range values {
		items = append(items, strconv.Itoa(value))
	}
	return strings.Join(items, ",")
}

func printList(label string, values []int) {
	fmt.Printf("%s (%d): %s\n", label, len(values), formatSyscalls(values))
}

func main() {
	detectedNetworkDisabledRaw := flag.String(
		"detected-network-disabled",
		"",
		"comma-separated detected syscall numbers with network disabled",
	)
	detectedNetworkEnabledRaw := flag.String(
		"detected-network-enabled",
		"",
		"comma-separated detected syscall numbers with network enabled",
	)
	flag.Parse()

	detectedNetworkDisabled, err := parseSyscalls(*detectedNetworkDisabledRaw)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	detectedNetworkEnabled, err := parseSyscalls(*detectedNetworkEnabledRaw)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}

	defaultAllowed := uniqueSorted(python_syscall.ALLOW_SYSCALLS)
	networkAllowed := uniqueSorted(python_syscall.ALLOW_NETWORK_SYSCALLS)
	errorSyscalls := uniqueSorted(python_syscall.ALLOW_ERROR_SYSCALLS)
	effectiveAllowed := uniqueSorted(defaultAllowed, networkAllowed)

	fmt.Println()
	fmt.Println("Syscall comparison (amd64)")
	printList("Default allowed", defaultAllowed)
	printList("Network allowed", networkAllowed)
	printList("EPERM instead of kill", errorSyscalls)

	fmt.Println()
	fmt.Println("enable_network=false")
	printList("Effective allowed", defaultAllowed)
	printList("Detected required", detectedNetworkDisabled)
	printList("Already allowed", intersect(detectedNetworkDisabled, defaultAllowed))
	printList("Additional required", difference(detectedNetworkDisabled, defaultAllowed))

	fmt.Println()
	fmt.Println("enable_network=true")
	printList("Effective allowed", effectiveAllowed)
	printList("Detected required", detectedNetworkEnabled)
	printList("Already allowed", intersect(detectedNetworkEnabled, effectiveAllowed))
	printList("Additional required", difference(detectedNetworkEnabled, effectiveAllowed))
}
